from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.engineer import Engineer
from app.models.applications import Application
from app.models.verification import EngineerApplicationAccess
from app.models.audit import AuditLog
from app.auth import require_supervisor


router = APIRouter()


# ============================================================
# CONSTANTS
# ============================================================

DEFAULT_ARM_STATUS = "Not Started"


# ============================================================
# REQUEST MODELS
# ============================================================

class EngineerCreateRequest(BaseModel):
    alias: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=200)
    email: Optional[str] = Field(default=None, max_length=255)
    level: Optional[str] = Field(default=None, max_length=50)
    rm_email: Optional[str] = Field(default=None, max_length=255)
    role: str = Field(default="ENGINEER", max_length=50)


class EngineerUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, max_length=200)
    email: Optional[str] = Field(default=None, max_length=255)
    level: Optional[str] = Field(default=None, max_length=50)
    rm_email: Optional[str] = Field(default=None, max_length=255)
    role: Optional[str] = Field(default=None, max_length=50)


# ============================================================
# HELPERS
# ============================================================

def validate_role(role: Optional[str]) -> str:

    value = (role or "ENGINEER").strip().upper()

    if value not in {"ENGINEER", "SUPERVISOR"}:
        raise HTTPException(
            status_code=400,
            detail="Role must be ENGINEER or SUPERVISOR.",
        )

    return value


def audit(
    db: Session,
    engineer_id: Optional[int],
    action: str,
    old_status: Optional[str],
    new_status: Optional[str],
    remarks: Optional[str],
    performed_by: str,
):

    db.add(
        AuditLog(
            engineer_id=engineer_id,
            application_id=None,
            action=action,
            old_status=old_status,
            new_status=new_status,
            remarks=remarks,
            performed_by=performed_by,
        )
    )


def assign_active_applications(
    db: Session,
    engineer: Engineer,
) -> int:

    # Supervisors are portal administrators.
    # Applications are assigned to engineers only.
    if str(engineer.role or "").upper() != "ENGINEER":
        return 0

    applications = (
        db.query(Application)
        .filter(Application.active == True)
        .all()
    )

    existing = (
        db.query(EngineerApplicationAccess)
        .filter(
            EngineerApplicationAccess.engineer_id
            == engineer.id
        )
        .all()
    )

    existing_ids = {
        row.application_id
        for row in existing
    }

    assigned = 0

    for application in applications:

        if application.id in existing_ids:
            continue

        db.add(
            EngineerApplicationAccess(
                engineer_id=engineer.id,
                application_id=application.id,
                access_status="Required",
                verification_status="Pending",
                ticket_status=DEFAULT_ARM_STATUS,
            )
        )

        assigned += 1

    return assigned


# ============================================================
# LIST ENGINEERS
# ============================================================

@router.get("/api/supervisor/engineers")
def list_engineers(
    db: Session = Depends(get_db),
    current_user: Engineer = Depends(require_supervisor),
):

    engineers = (
        db.query(Engineer)
        .order_by(
            Engineer.active.desc(),
            Engineer.name.asc(),
        )
        .all()
    )

    result = []

    for engineer in engineers:

        application_count = (
            db.query(EngineerApplicationAccess)
            .filter(
                EngineerApplicationAccess.engineer_id
                == engineer.id
            )
            .count()
        )

        result.append(
            {
                "id": engineer.id,
                "alias": engineer.alias,
                "name": engineer.name,
                "email": engineer.email,
                "level": engineer.level,
                "rm_email": engineer.rm_email,
                "role": engineer.role,
                "active": bool(engineer.active),
                "application_count": application_count,
            }
        )

    return result


# Keep compatibility with the UI we already added.
@router.get("/api/supervisor/engineers/manage")
def list_engineers_manage(
    db: Session = Depends(get_db),
    current_user: Engineer = Depends(require_supervisor),
):

    return list_engineers(
        db=db,
        current_user=current_user,
    )


# ============================================================
# ADD ENGINEER / SUPERVISOR
# ============================================================

@router.post("/api/supervisor/engineers")
def create_engineer(
    data: EngineerCreateRequest,
    db: Session = Depends(get_db),
    current_user: Engineer = Depends(require_supervisor),
):

    alias = data.alias.strip()
    name = data.name.strip()
    role = validate_role(data.role)

    if not alias:
        raise HTTPException(
            status_code=400,
            detail="Alias is required.",
        )

    if not name:
        raise HTTPException(
            status_code=400,
            detail="Name is required.",
        )

    existing = (
        db.query(Engineer)
        .filter(
            Engineer.alias.ilike(alias)
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Engineer alias '{alias}' "
                "already exists."
            ),
        )

    engineer = Engineer(
        alias=alias,
        name=name,
        email=(
            data.email.strip()
            if data.email and data.email.strip()
            else None
        ),
        level=(
            data.level.strip()
            if data.level and data.level.strip()
            else None
        ),
        rm_email=(
            data.rm_email.strip()
            if data.rm_email and data.rm_email.strip()
            else None
        ),
        role=role,
        active=True,
        must_set_password=True,
    )

    db.add(engineer)
    db.flush()

    assigned = assign_active_applications(
        db,
        engineer,
    )

    performed_by = (
        current_user.alias
        or current_user.email
        or current_user.name
    )

    audit(
        db,
        engineer.id,
        "ENGINEER_CREATED",
        None,
        role,
        (
            f"{role.title()} '{name}' created. "
            f"{assigned} active applications assigned."
        ),
        performed_by,
    )

    try:

        db.commit()
        db.refresh(engineer)

    except Exception as exc:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Unable to create engineer: {exc}",
        )

    return {
        "message": (
            f"{role.title()} '{name}' "
            "created successfully."
        ),
        "engineer": {
            "id": engineer.id,
            "alias": engineer.alias,
            "name": engineer.name,
            "email": engineer.email,
            "level": engineer.level,
            "rm_email": engineer.rm_email,
            "role": engineer.role,
            "active": bool(engineer.active),
        },
        "applications_assigned": assigned,
    }


# ============================================================
# EDIT ENGINEER / SUPERVISOR
# ============================================================

@router.patch("/api/supervisor/engineers/{engineer_id}")
def update_engineer(
    engineer_id: int,
    data: EngineerUpdateRequest,
    db: Session = Depends(get_db),
    current_user: Engineer = Depends(require_supervisor),
):

    engineer = (
        db.query(Engineer)
        .filter(
            Engineer.id == engineer_id
        )
        .first()
    )

    if engineer is None:
        raise HTTPException(
            status_code=404,
            detail="Engineer not found.",
        )

    old_role = engineer.role

    if data.name is not None:

        name = data.name.strip()

        if not name:
            raise HTTPException(
                status_code=400,
                detail="Name cannot be empty.",
            )

        engineer.name = name

    if data.email is not None:
        engineer.email = (
            data.email.strip() or None
        )

    if data.level is not None:
        engineer.level = (
            data.level.strip() or None
        )

    if data.rm_email is not None:
        engineer.rm_email = (
            data.rm_email.strip() or None
        )

    if data.role is not None:

        engineer.role = validate_role(
            data.role
        )

    assigned = assign_active_applications(
        db,
        engineer,
    )

    performed_by = (
        current_user.alias
        or current_user.email
        or current_user.name
    )

    audit(
        db,
        engineer.id,
        "ENGINEER_UPDATED",
        old_role,
        engineer.role,
        (
            f"Engineer '{engineer.alias}' updated. "
            f"{assigned} missing applications restored."
        ),
        performed_by,
    )

    try:

        db.commit()
        db.refresh(engineer)

    except Exception as exc:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Unable to update engineer: {exc}",
        )

    return {
        "message": (
            f"Engineer '{engineer.name}' "
            "updated successfully."
        ),
        "applications_restored": assigned,
    }


# ============================================================
# REMOVE / DEACTIVATE ENGINEER
#
# IMPORTANT:
# We do NOT physically delete the engineer.
# Historical access and audit records remain intact.
# ============================================================

@router.delete("/api/supervisor/engineers/{engineer_id}")
def deactivate_engineer(
    engineer_id: int,
    db: Session = Depends(get_db),
    current_user: Engineer = Depends(require_supervisor),
):

    if current_user.id == engineer_id:

        raise HTTPException(
            status_code=400,
            detail=(
                "You cannot remove your own "
                "supervisor account."
            ),
        )

    engineer = (
        db.query(Engineer)
        .filter(
            Engineer.id == engineer_id
        )
        .first()
    )

    if engineer is None:
        raise HTTPException(
            status_code=404,
            detail="Engineer not found.",
        )

    if not engineer.active:

        return {
            "message": (
                f"Engineer '{engineer.name}' "
                "is already inactive."
            )
        }

    engineer.active = False

    performed_by = (
        current_user.alias
        or current_user.email
        or current_user.name
    )

    audit(
        db,
        engineer.id,
        "ENGINEER_DEACTIVATED",
        "Active",
        "Inactive",
        (
            f"Engineer '{engineer.alias}' "
            "removed from active portal users. "
            "Historical access records retained."
        ),
        performed_by,
    )

    try:

        db.commit()

    except Exception as exc:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Unable to remove engineer: {exc}",
        )

    return {
        "message": (
            f"Engineer '{engineer.name}' "
            "removed successfully."
        )
    }


# ============================================================
# REACTIVATE ENGINEER
# ============================================================

@router.post(
    "/api/supervisor/engineers/{engineer_id}/reactivate"
)
def reactivate_engineer(
    engineer_id: int,
    db: Session = Depends(get_db),
    current_user: Engineer = Depends(require_supervisor),
):

    engineer = (
        db.query(Engineer)
        .filter(
            Engineer.id == engineer_id
        )
        .first()
    )

    if engineer is None:
        raise HTTPException(
            status_code=404,
            detail="Engineer not found.",
        )

    engineer.active = True

    assigned = assign_active_applications(
        db,
        engineer,
    )

    performed_by = (
        current_user.alias
        or current_user.email
        or current_user.name
    )

    audit(
        db,
        engineer.id,
        "ENGINEER_REACTIVATED",
        "Inactive",
        "Active",
        (
            f"Engineer '{engineer.alias}' "
            f"reactivated. {assigned} applications restored."
        ),
        performed_by,
    )

    try:

        db.commit()

    except Exception as exc:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Unable to reactivate engineer: {exc}",
        )

    return {
        "message": (
            f"Engineer '{engineer.name}' "
            "reactivated successfully."
        ),
        "applications_restored": assigned,
    }