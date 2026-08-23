from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.applications import Application
from app.models.audit import AuditLog
from app.models.engineer import Engineer
from app.models.verification import EngineerApplicationAccess


router = APIRouter()


# ============================================================
# CONSTANTS
# ============================================================

DEFAULT_ARM_STATUS = "Not Required"

VALID_VERIFICATION_STATUSES = {
    "Verified",
    "Issue",
    "Pending",
}

VALID_ARM_STATUSES = {
    "Request Not Initiated",
    "Not Required",
    "Approval Pending",
    "Completed",
}


# ============================================================
# NORMAL ENGINEER VERIFICATION REQUEST
# ============================================================

class VerificationUpdate(BaseModel):
    status: str = Field(
        ...,
        min_length=1,
        max_length=50,
    )

    remarks: Optional[str] = Field(
        default=None,
        max_length=200,
    )

    performed_by: Optional[str] = Field(
        default=None,
        max_length=200,
    )


# ============================================================
# SUPERVISOR ARM UPDATE REQUEST
# ============================================================

class ArmUpdate(BaseModel):
    arm_ticket: Optional[str] = Field(
        default=None,
        max_length=100,
    )

    ticket_status: str = Field(
        ...,
        min_length=1,
        max_length=50,
    )


# ============================================================
# CREATE AUDIT ENTRY
# ============================================================

def create_audit_entry(
    db: Session,
    engineer_id: int,
    application_id: int,
    action: str,
    old_status: Optional[str],
    new_status: Optional[str],
    remarks: Optional[str],
    performed_by: Optional[str],
):
    audit = AuditLog(
        engineer_id=engineer_id,
        application_id=application_id,
        action=action,
        old_status=old_status,
        new_status=new_status,
        remarks=remarks,
        performed_by=performed_by,
    )

    db.add(audit)


# ============================================================
# GET ENGINEER ACCESS
# ============================================================

@router.get("/engineers/{engineer_id}/access")
def get_engineer_access(
    engineer_id: int,
    db: Session = Depends(get_db),
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
        raise HTTPException(
            status_code=404,
            detail="Engineer not found",
        )

    records = (
        db.query(EngineerApplicationAccess)
        .filter(
            EngineerApplicationAccess.engineer_id == engineer_id
        )
        .order_by(
            EngineerApplicationAccess.application_id
        )
        .all()
    )

    applications = []

    for access in records:

        application = (
            db.query(Application)
            .filter(
                Application.id == access.application_id
            )
            .first()
        )

        if application is None:
            continue

        verification_status = (
            access.verification_status
            or "Pending"
        )

        if verification_status not in VALID_VERIFICATION_STATUSES:
            verification_status = "Pending"

        ticket_status = (
            access.ticket_status
            or DEFAULT_ARM_STATUS
        )

        if ticket_status not in VALID_ARM_STATUSES:
            ticket_status = DEFAULT_ARM_STATUS

        applications.append(
            {
                "access_id": access.id,
                "application_id": application.id,
                "application_name": application.name,
                "access_status": access.access_status,
                "verification_status": verification_status,
                "arm_ticket": access.arm_ticket,
                "ticket_status": ticket_status,
                "last_verified_date": (
                    access.last_verified_date.isoformat()
                    if access.last_verified_date
                    else None
                ),
                "remarks": access.remarks,
            }
        )

    return {
        "engineer_id": engineer.id,
        "engineer_name": engineer.name,
        "level": engineer.level,
        "email": engineer.email,
        "applications": applications,
    }


# ============================================================
# NORMAL ENGINEER UPDATE
# ARM DETAILS ARE NOT UPDATED HERE
# ============================================================

@router.patch("/verification/{engineer_id}/{application_id}")
def update_verification(
    engineer_id: int,
    application_id: int,
    data: VerificationUpdate,
    db: Session = Depends(get_db),
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
        raise HTTPException(
            status_code=404,
            detail="Engineer not found",
        )

    application = (
        db.query(Application)
        .filter(
            Application.id == application_id,
            Application.active == True,
        )
        .first()
    )

    if application is None:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    access = (
        db.query(EngineerApplicationAccess)
        .filter(
            EngineerApplicationAccess.engineer_id == engineer_id,
            EngineerApplicationAccess.application_id == application_id,
        )
        .first()
    )

    if access is None:
        raise HTTPException(
            status_code=404,
            detail="Application access record not found",
        )

    status = data.status.strip()

    if status not in VALID_VERIFICATION_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid verification status. "
                "Allowed values: Verified, Issue, Pending"
            ),
        )

    remarks = (
        data.remarks.strip()
        if data.remarks and data.remarks.strip()
        else None
    )

    # Remarks are mandatory only when Issue is selected.
    if status == "Issue" and not remarks:
        raise HTTPException(
            status_code=400,
            detail="Remarks are required when verification status is Issue",
        )

    old_status = access.verification_status or "Pending"
    old_remarks = access.remarks

    access.verification_status = status
    access.remarks = remarks

    if status in {"Verified", "Issue"}:
        access.last_verified_date = datetime.now(
            ZoneInfo("Asia/Kolkata")
        )
    else:
        access.last_verified_date = None

    performed_by = (
        data.performed_by
        or engineer.alias
        or engineer.email
        or engineer.name
    )

    if old_status != status:
        create_audit_entry(
            db=db,
            engineer_id=engineer_id,
            application_id=application_id,
            action="VERIFICATION_STATUS_CHANGED",
            old_status=old_status,
            new_status=status,
            remarks=access.remarks,
            performed_by=performed_by,
        )

    if old_remarks != access.remarks:
        create_audit_entry(
            db=db,
            engineer_id=engineer_id,
            application_id=application_id,
            action="REMARKS_UPDATED",
            old_status=None,
            new_status=None,
            remarks=access.remarks,
            performed_by=performed_by,
        )

    try:
        db.commit()
        db.refresh(access)

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Unable to save verification changes: {exc}",
        )

    return {
        "message": "Verification updated successfully",
        "verification_status": access.verification_status,
        "remarks": access.remarks,
        "last_verified_date": (
            access.last_verified_date.isoformat()
            if access.last_verified_date
            else None
        ),
        "arm_ticket": access.arm_ticket,
        "ticket_status": (
            access.ticket_status
            or DEFAULT_ARM_STATUS
        ),
    }


# ============================================================
# SUPERVISOR ARM UPDATE
#
# IMPORTANT:
# A valid supervisor can update ARM details for the engineer
# selected from the Supervisor Dashboard.
#
# We intentionally DO NOT check:
#
# engineer.supervisor_id != supervisor.id
#
# because that was causing:
#
# "This engineer is not assigned to the current supervisor"
#
# ============================================================

@router.patch(
    "/supervisor/{supervisor_id}/engineer/"
    "{engineer_id}/application/{application_id}/arm"
)
def update_arm_details(
    supervisor_id: int,
    engineer_id: int,
    application_id: int,
    data: ArmUpdate,
    db: Session = Depends(get_db),
):
    supervisor = (
        db.query(Engineer)
        .filter(
            Engineer.id == supervisor_id,
            Engineer.role == "SUPERVISOR",
            Engineer.active == True,
        )
        .first()
    )

    if supervisor is None:
        raise HTTPException(
            status_code=403,
            detail="Valid supervisor not found",
        )

    engineer = (
        db.query(Engineer)
        .filter(
            Engineer.id == engineer_id,
            Engineer.active == True,
        )
        .first()
    )

    if engineer is None:
        raise HTTPException(
            status_code=404,
            detail="Engineer not found",
        )

    application = (
        db.query(Application)
        .filter(
            Application.id == application_id,
            Application.active == True,
        )
        .first()
    )

    if application is None:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    access = (
        db.query(EngineerApplicationAccess)
        .filter(
            EngineerApplicationAccess.engineer_id == engineer_id,
            EngineerApplicationAccess.application_id == application_id,
        )
        .first()
    )

    if access is None:
        raise HTTPException(
            status_code=404,
            detail="Application access record not found",
        )

    ticket_status = data.ticket_status.strip()

    if ticket_status not in VALID_ARM_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid ARM request status. Allowed values: "
                "Request Not Initiated, Not Required, "
                "Approval Pending, Completed"
            ),
        )

    old_arm_ticket = access.arm_ticket

    old_ticket_status = (
        access.ticket_status
        or DEFAULT_ARM_STATUS
    )

    access.arm_ticket = (
        data.arm_ticket.strip()
        if data.arm_ticket and data.arm_ticket.strip()
        else None
    )

    access.ticket_status = ticket_status

    performed_by = (
        supervisor.alias
        or supervisor.email
        or supervisor.name
    )

    if old_arm_ticket != access.arm_ticket:
        create_audit_entry(
            db=db,
            engineer_id=engineer_id,
            application_id=application_id,
            action="ARM_REQUEST_UPDATED",
            old_status=old_arm_ticket,
            new_status=access.arm_ticket,
            remarks=None,
            performed_by=performed_by,
        )

    if old_ticket_status != ticket_status:
        create_audit_entry(
            db=db,
            engineer_id=engineer_id,
            application_id=application_id,
            action="ARM_TICKET_STATUS_CHANGED",
            old_status=old_ticket_status,
            new_status=ticket_status,
            remarks=access.arm_ticket,
            performed_by=performed_by,
        )

    try:
        db.commit()
        db.refresh(access)

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Unable to update ARM details: {exc}",
        )

    return {
        "message": "ARM details updated successfully",
        "engineer_id": engineer_id,
        "application_id": application_id,
        "arm_ticket": access.arm_ticket,
        "ticket_status": (
            access.ticket_status
            or DEFAULT_ARM_STATUS
        ),
    }


# ============================================================
# SUPERVISOR RESET APPLICATION
#
# Same fix:
# No engineer.supervisor_id validation.
# ============================================================

@router.patch(
    "/supervisor/{supervisor_id}/engineer/"
    "{engineer_id}/application/{application_id}/reset"
)
def reset_application(
    supervisor_id: int,
    engineer_id: int,
    application_id: int,
    db: Session = Depends(get_db),
):
    supervisor = (
        db.query(Engineer)
        .filter(
            Engineer.id == supervisor_id,
            Engineer.role == "SUPERVISOR",
            Engineer.active == True,
        )
        .first()
    )

    if supervisor is None:
        raise HTTPException(
            status_code=403,
            detail="Valid supervisor not found",
        )

    engineer = (
        db.query(Engineer)
        .filter(
            Engineer.id == engineer_id,
            Engineer.active == True,
        )
        .first()
    )

    if engineer is None:
        raise HTTPException(
            status_code=404,
            detail="Engineer not found",
        )

    access = (
        db.query(EngineerApplicationAccess)
        .filter(
            EngineerApplicationAccess.engineer_id == engineer_id,
            EngineerApplicationAccess.application_id == application_id,
        )
        .first()
    )

    if access is None:
        raise HTTPException(
            status_code=404,
            detail="Application access record not found",
        )

    old_verification = (
        access.verification_status
        or "Pending"
    )

    old_arm = access.arm_ticket

    old_ticket_status = (
        access.ticket_status
        or DEFAULT_ARM_STATUS
    )

    performed_by = (
        supervisor.alias
        or supervisor.email
        or supervisor.name
    )

    access.verification_status = "Pending"
    access.remarks = None
    access.last_verified_date = None
    access.arm_ticket = None
    access.ticket_status = DEFAULT_ARM_STATUS

    if old_verification != "Pending":
        create_audit_entry(
            db=db,
            engineer_id=engineer_id,
            application_id=application_id,
            action="APPLICATION_RESET",
            old_status=old_verification,
            new_status="Pending",
            remarks=None,
            performed_by=performed_by,
        )

    if (
        old_arm
        or old_ticket_status != DEFAULT_ARM_STATUS
    ):
        create_audit_entry(
            db=db,
            engineer_id=engineer_id,
            application_id=application_id,
            action="ARM_RESET",
            old_status=old_ticket_status,
            new_status=DEFAULT_ARM_STATUS,
            remarks=old_arm,
            performed_by=performed_by,
        )

    try:
        db.commit()
        db.refresh(access)

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Unable to reset application: {exc}",
        )

    return {
        "message": "Application status reset successfully",
        "engineer_id": engineer_id,
        "application_id": application_id,
        "verification_status": access.verification_status,
        "remarks": access.remarks,
        "last_verified_date": None,
        "arm_ticket": None,
        "ticket_status": (
            access.ticket_status
            or DEFAULT_ARM_STATUS
        ),
    }