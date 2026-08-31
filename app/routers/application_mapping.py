from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_engineer, require_supervisor
from app.database import get_db
from app.models.applications import Application
from app.models.application_tier_access import ApplicationTierAccess
from app.models.engineer import Engineer
from app.models.verification import EngineerApplicationAccess


router = APIRouter()


IM_ABOVE_LEVELS = {"IM", "QM", "TL"}


def level_allows_mapping(level, mapping, role=None):
    """Return whether a level/role is allowed the application."""
    normalized_role = str(role or "").strip().upper()
    normalized_level = str(level or "").strip().upper()

    # Supervisors receive the IM & Above application set regardless
    # of their stored engineer level (for example, a supervisor may
    # remain recorded as L3 in the organizational roster).
    if normalized_role == "SUPERVISOR":
        return bool(mapping.im_above_access)

    if normalized_level == "L1":
        return bool(mapping.tier1_access)
    if normalized_level == "L2":
        return bool(mapping.tier2_access)
    if normalized_level == "L3":
        return bool(mapping.tier3_access)
    if normalized_level in IM_ABOVE_LEVELS:
        return bool(mapping.im_above_access)

    return False


def build_engineer_applications(engineer_id: int, db: Session):
    engineer = (
        db.query(Engineer)
        .filter(
            Engineer.id == engineer_id,
            Engineer.active == True,
        )
        .first()
    )

    if engineer is None:
        raise HTTPException(status_code=404, detail="Engineer not found")

    rows = (
        db.query(
            EngineerApplicationAccess,
            Application,
            ApplicationTierAccess,
        )
        .join(
            Application,
            Application.id == EngineerApplicationAccess.application_id,
        )
        .join(
            ApplicationTierAccess,
            ApplicationTierAccess.application_id == Application.id,
        )
        .filter(
            EngineerApplicationAccess.engineer_id == engineer_id,
            Application.active == True,
            ApplicationTierAccess.active == True,
        )
        .order_by(ApplicationTierAccess.display_name)
        .all()
    )

    applications = []

    for access, application, mapping in rows:
        if not level_allows_mapping(
            engineer.level,
            mapping,
            engineer.role,
        ):
            continue

        applications.append(
            {
                "access_id": access.id,
                "application_id": application.id,
                "application_name": mapping.display_name,
                "access_status": access.access_status,
                "verification_status": access.verification_status or "Pending",
                "arm_ticket": access.arm_ticket or "",
                "ticket_status": access.ticket_status or "Not Started",
                "last_verified_date": (
                    access.last_verified_date.isoformat()
                    if access.last_verified_date
                    else None
                ),
                "remarks": access.remarks or "",
            }
        )

    return applications


def engineer_payload(engineer: Engineer, db: Session):
    applications = build_engineer_applications(engineer.id, db)

    verified = sum(
        1 for item in applications
        if item["verification_status"] == "Verified"
    )
    pending = sum(
        1 for item in applications
        if item["verification_status"] == "Pending"
    )
    issues = sum(
        1 for item in applications
        if item["verification_status"] == "Issue"
    )

    return {
        "engineer_id": engineer.id,
        "engineer_name": engineer.name,
        "name": engineer.name,
        "alias": engineer.alias,
        "level": engineer.level,
        "email": engineer.email,
        "role": engineer.role,
        "applications": applications,
        "total": len(applications),
        "summary": {
            "total": len(applications),
            "verified": verified,
            "pending": pending,
            "issues": issues,
        },
    }


@router.get("/api/supervisor/engineers")
def supervisor_engineers(
    db: Session = Depends(get_db),
    current_user: Engineer = Depends(require_supervisor),
):
    engineers = (
        db.query(Engineer)
        .filter(
            Engineer.active == True,
        )
        .order_by(Engineer.name)
        .all()
    )

    result = []

    for engineer in engineers:
        if str(engineer.role or "").upper() == "SUPERVISOR":
            continue

        applications = build_engineer_applications(engineer.id, db)

        result.append(
            {
                "id": engineer.id,
                "name": engineer.name,
                "alias": engineer.alias,
                "level": engineer.level,
                "email": engineer.email,
                "role": engineer.role,
                "total": len(applications),
                "application_count": len(applications),
                "display_name": (
                    f"{engineer.name} ({engineer.alias}) - "
                    f"{engineer.level} [{len(applications)} Apps]"
                ),
            }
        )

    return result


@router.get("/api/supervisor/engineer/{engineer_id}")
def supervisor_engineer(
    engineer_id: int,
    db: Session = Depends(get_db),
    current_user: Engineer = Depends(require_supervisor),
):
    engineer = (
        db.query(Engineer)
        .filter(
            Engineer.id == engineer_id,
            Engineer.active == True,
        )
        .first()
    )

    if engineer is None:
        raise HTTPException(status_code=404, detail="Engineer not found")

    return engineer_payload(engineer, db)


@router.get("/api/engineer/{engineer_id}")
def engineer_details(
    engineer_id: int,
    db: Session = Depends(get_db),
    current_user: Engineer = Depends(get_current_engineer),
):
    if current_user.id != engineer_id and str(current_user.role or "").upper() != "SUPERVISOR":
        raise HTTPException(status_code=403, detail="Not authorized")

    engineer = (
        db.query(Engineer)
        .filter(
            Engineer.id == engineer_id,
            Engineer.active == True,
        )
        .first()
    )

    if engineer is None:
        raise HTTPException(status_code=404, detail="Engineer not found")

    return engineer_payload(engineer, db)


@router.get("/api/application-mapping")
def application_mapping(
    db: Session = Depends(get_db),
    current_user: Engineer = Depends(require_supervisor),
):
    rows = (
        db.query(ApplicationTierAccess, Application)
        .join(Application, Application.id == ApplicationTierAccess.application_id)
        .filter(
            ApplicationTierAccess.active == True,
            Application.active == True,
        )
        .order_by(ApplicationTierAccess.display_name)
        .all()
    )

    return [
        {
            "application_id": mapping.application_id,
            "application_name": mapping.display_name,
            "source_label": mapping.source_label,
            "tier1": bool(mapping.tier1_access),
            "tier2": bool(mapping.tier2_access),
            "tier3": bool(mapping.tier3_access),
            "im_above": bool(mapping.im_above_access),
        }
        for mapping, application in rows
    ]
