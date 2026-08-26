from pathlib import Path
import re
import shutil
from datetime import datetime


# ============================================================
# CONFIG
# ============================================================

ROOT = Path(__file__).resolve().parent

VERIFICATION = ROOT / "app" / "routers" / "verification.py"
SUPERVISOR_HTML = ROOT / "app" / "templates" / "supervisor.html"


# ============================================================
# BACKUP
# ============================================================

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

verification_backup = (
    ROOT / f"verification.py.backup_{timestamp}"
)

supervisor_backup = (
    ROOT / f"supervisor.html.backup_{timestamp}"
)

print()
print("=" * 70)
print("ACCESS APPLICATION MANAGEMENT FIX")
print("=" * 70)
print()

if not VERIFICATION.exists():
    raise FileNotFoundError(
        f"File not found: {VERIFICATION}"
    )

if not SUPERVISOR_HTML.exists():
    raise FileNotFoundError(
        f"File not found: {SUPERVISOR_HTML}"
    )


shutil.copy2(
    VERIFICATION,
    verification_backup
)

shutil.copy2(
    SUPERVISOR_HTML,
    supervisor_backup
)

print(f"[OK] Backup created:")
print(f"     {verification_backup}")
print(f"     {supervisor_backup}")
print()


# ============================================================
# NEW APPLICATION MANAGEMENT BACKEND
# ============================================================

APPLICATION_MANAGEMENT_CODE = r'''

# ============================================================
# SUPERVISOR APPLICATION MANAGEMENT
# ============================================================


@router.get("/api/supervisor/applications")
def list_supervisor_applications(
    db: Session = Depends(get_db),
    current_user: Engineer = Depends(require_supervisor),
):

    applications = (
        db.query(Application)
        .filter(Application.active == True)
        .order_by(Application.name)
        .all()
    )

    return [
        {
            "id": application.id,
            "name": application.name,
            "description": application.description,
            "active": application.active,
        }
        for application in applications
    ]


# ============================================================
# ADD APPLICATION FOR ALL ENGINEERS
# ============================================================

@router.post("/api/supervisor/applications")
def create_application_for_all_engineers(
    data: ApplicationCreate,
    db: Session = Depends(get_db),
    current_user: Engineer = Depends(require_supervisor),
):

    supervisor = current_user

    name = data.name.strip()

    access_status = (
        data.access_status.strip()
        if data.access_status
        else "Required"
    )

    description = (
        (data.description or "").strip()
        or None
    )

    if not name:
        raise HTTPException(
            status_code=400,
            detail="Application name is required.",
        )

    if not access_status:
        access_status = "Required"

    # --------------------------------------------------------
    # Find existing application
    # --------------------------------------------------------

    application = (
        db.query(Application)
        .filter(
            Application.name.ilike(name)
        )
        .first()
    )

    # --------------------------------------------------------
    # Create application
    # --------------------------------------------------------

    if application is None:

        application = Application(
            name=name,
            description=description,
            active=True,
        )

        db.add(application)
        db.flush()

    else:

        # Reactivate previously removed application.
        application.active = True

        if description:
            application.description = description

    # --------------------------------------------------------
    # Get active engineers
    # --------------------------------------------------------

    engineers = (
        db.query(Engineer)
        .filter(
            Engineer.active == True,
            Engineer.role != "SUPERVISOR",
        )
        .all()
    )

    # --------------------------------------------------------
    # Existing assignments
    # --------------------------------------------------------

    existing_rows = (
        db.query(EngineerApplicationAccess)
        .filter(
            EngineerApplicationAccess.application_id
            == application.id
        )
        .all()
    )

    existing_engineer_ids = {
        row.engineer_id
        for row in existing_rows
    }

    # --------------------------------------------------------
    # Create missing assignments
    # --------------------------------------------------------

    assigned = 0

    for engineer in engineers:

        if engineer.id not in existing_engineer_ids:

            db.add(
                EngineerApplicationAccess(
                    engineer_id=engineer.id,
                    application_id=application.id,
                    access_status=access_status,
                    verification_status="Pending",
                    ticket_status=DEFAULT_ARM_STATUS,
                )
            )

            assigned += 1

    # --------------------------------------------------------
    # Audit
    # --------------------------------------------------------

    create_audit_entry(
        db,
        None,
        application.id,
        "APPLICATION_CREATED_FOR_ALL_ENGINEERS",
        None,
        application.name,
        (
            f"Assigned to {assigned} engineers; "
            f"access status: {access_status}"
        ),
        supervisor.alias
        or supervisor.email
        or supervisor.name,
    )

    try:

        db.commit()
        db.refresh(application)

    except Exception as exc:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Unable to add application: {exc}",
        )

    return {
        "message": (
            f"Application '{application.name}' "
            "added for all engineers."
        ),
        "application_id": application.id,
        "assigned": assigned,
    }


# ============================================================
# REMOVE APPLICATION FOR ALL ENGINEERS
# ============================================================

@router.delete(
    "/api/supervisor/applications/{application_id}"
)
def remove_application_for_all_engineers(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: Engineer = Depends(require_supervisor),
):

    supervisor = current_user

    # IMPORTANT:
    # Do NOT require active=True here.
    # We need the actual application record.

    application = (
        db.query(Application)
        .filter(
            Application.id == application_id
        )
        .first()
    )

    if application is None:

        raise HTTPException(
            status_code=404,
            detail="Application not found.",
        )

    if not application.active:

        return {
            "message": (
                f"Application '{application.name}' "
                "is already removed for all engineers."
            )
        }

    application_name = application.name

    # --------------------------------------------------------
    # Deactivate master application
    #
    # Keep access records for audit/history.
    # --------------------------------------------------------

    application.active = False

    create_audit_entry(
        db,
        None,
        application_id,
        "APPLICATION_REMOVED_FOR_ALL_ENGINEERS",
        application_name,
        None,
        (
            "Application deactivated globally. "
            "Engineer access history retained."
        ),
        supervisor.alias
        or supervisor.email
        or supervisor.name,
    )

    try:

        db.commit()

    except Exception as exc:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to remove application "
                f"for all engineers: {exc}"
            ),
        )

    return {
        "message": (
            f"Application '{application_name}' "
            "removed for all engineers."
        )
    }


# ============================================================
# ADD APPLICATION TO ONE ENGINEER
# ============================================================

@router.post(
    "/api/supervisor/engineer/{engineer_id}/application"
)
def assign_application_to_engineer_by_supervisor(
    engineer_id: int,
    data: ApplicationCreate,
    db: Session = Depends(get_db),
    current_user: Engineer = Depends(require_supervisor),
):

    supervisor = current_user

    # --------------------------------------------------------
    # Validate engineer
    # --------------------------------------------------------

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
            detail="Engineer not found.",
        )

    name = data.name.strip()

    access_status = (
        data.access_status.strip()
        if data.access_status
        else "Required"
    )

    description = (
        (data.description or "").strip()
        or None
    )

    if not name:

        raise HTTPException(
            status_code=400,
            detail="Application name is required.",
        )

    # --------------------------------------------------------
    # Find application
    # --------------------------------------------------------

    application = (
        db.query(Application)
        .filter(
            Application.name.ilike(name)
        )
        .first()
    )

    # --------------------------------------------------------
    # Create application if required
    # --------------------------------------------------------

    if application is None:

        application = Application(
            name=name,
            description=description,
            active=True,
        )

        db.add(application)
        db.flush()

    else:

        # Reactivate application if it was globally removed.

        application.active = True

        if description:
            application.description = description

    # --------------------------------------------------------
    # Check existing assignment
    # --------------------------------------------------------

    access = (
        db.query(EngineerApplicationAccess)
        .filter(
            EngineerApplicationAccess.engineer_id
            == engineer_id,
            EngineerApplicationAccess.application_id
            == application.id,
        )
        .first()
    )

    if access is not None:

        raise HTTPException(
            status_code=409,
            detail=(
                "This application is already "
                "assigned to this engineer."
            ),
        )

    # --------------------------------------------------------
    # Create assignment
    # --------------------------------------------------------

    db.add(
        EngineerApplicationAccess(
            engineer_id=engineer_id,
            application_id=application.id,
            access_status=access_status,
            verification_status="Pending",
            ticket_status=DEFAULT_ARM_STATUS,
        )
    )

    create_audit_entry(
        db,
        engineer_id,
        application.id,
        "APPLICATION_ASSIGNED_BY_SUPERVISOR",
        None,
        application.name,
        (
            f"Assigned to engineer "
            f"({access_status}) by supervisor."
        ),
        supervisor.alias
        or supervisor.email
        or supervisor.name,
    )

    try:

        db.commit()

    except Exception as exc:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Unable to assign application: {exc}",
        )

    return {
        "message": (
            f"Application '{application.name}' "
            "assigned to engineer."
        ),
        "application_id": application.id,
    }


# ============================================================
# REMOVE APPLICATION FROM ONE ENGINEER
# ============================================================

@router.delete(
    "/api/supervisor/engineer/{engineer_id}/application/{application_id}"
)
def remove_application_for_engineer(
    engineer_id: int,
    application_id: int,
    db: Session = Depends(get_db),
    current_user: Engineer = Depends(require_supervisor),
):

    supervisor = current_user

    # --------------------------------------------------------
    # Validate engineer
    # --------------------------------------------------------

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
            detail="Engineer not found.",
        )

    # --------------------------------------------------------
    # Find engineer/application assignment
    # --------------------------------------------------------

    access = (
        db.query(EngineerApplicationAccess)
        .filter(
            EngineerApplicationAccess.engineer_id
            == engineer_id,
            EngineerApplicationAccess.application_id
            == application_id,
        )
        .first()
    )

    if access is None:

        raise HTTPException(
            status_code=404,
            detail=(
                "Application is not assigned "
                "to this engineer."
            ),
        )

    # --------------------------------------------------------
    # Find master application
    #
    # Notice: NO active=True filter.
    # --------------------------------------------------------

    application = (
        db.query(Application)
        .filter(
            Application.id == application_id
        )
        .first()
    )

    application_name = (
        application.name
        if application
        else f"Application #{application_id}"
    )

    # --------------------------------------------------------
    # Audit
    # --------------------------------------------------------

    create_audit_entry(
        db,
        engineer_id,
        application_id,
        "APPLICATION_REMOVED_FROM_ENGINEER",
        access.access_status,
        None,
        (
            f"Removed '{application_name}' "
            "from this engineer only."
        ),
        supervisor.alias
        or supervisor.email
        or supervisor.name,
    )

    # --------------------------------------------------------
    # Delete ONLY this engineer's assignment
    # --------------------------------------------------------

    db.delete(access)

    try:

        db.commit()

    except Exception as exc:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to remove application "
                f"from engineer: {exc}"
            ),
        )

    return {
        "message": (
            f"Application '{application_name}' "
            "removed from the engineer."
        )
    }
'''


# ============================================================
# UPDATE verification.py
# ============================================================

print("[1/2] Updating verification.py ...")

verification_text = VERIFICATION.read_text(
    encoding="utf-8"
)

# The application-management section starts at this function.
# In the current repository it is at the end of the router.
marker = "def require_matching_supervisor("

position = verification_text.find(marker)

if position == -1:

    raise RuntimeError(
        "Could not find the old application-management "
        "section in verification.py.\n"
        "No changes were made."
    )

# Preserve everything before application management.
prefix = verification_text[:position]

# Remove any trailing whitespace.
prefix = prefix.rstrip()

new_verification = (
    prefix
    + "\n\n"
    + APPLICATION_MANAGEMENT_CODE.strip()
    + "\n"
)

VERIFICATION.write_text(
    new_verification,
    encoding="utf-8"
)

print("[OK] verification.py updated.")
print()


# ============================================================
# UPDATE supervisor.html
# ============================================================

print("[2/2] Updating supervisor.html ...")

html = SUPERVISOR_HTML.read_text(
    encoding="utf-8"
)

original_html = html


# ------------------------------------------------------------
# Remove old supervisor_id from canonical application URLs.
#
# These replacements are intentionally limited to the
# application-management API URLs.
# ------------------------------------------------------------

replacements = [

    (
        r"/api/supervisor/\$\{SUPERVISOR_ID\}/applications",
        "/api/supervisor/applications",
    ),

    (
        r"/api/supervisor/\$\{supervisorId\}/applications",
        "/api/supervisor/applications",
    ),

    (
        r"/api/supervisor/\$\{SUPERVISOR_ID\}/engineer/\$\{engineerId\}/application",
        "/api/supervisor/engineer/${engineerId}/application",
    ),

    (
        r"/api/supervisor/\$\{supervisorId\}/engineer/\$\{engineerId\}/application",
        "/api/supervisor/engineer/${engineerId}/application",
    ),

]


for pattern, replacement in replacements:

    html, count = re.subn(
        pattern,
        replacement,
        html,
    )

    if count:
        print(
            f"[OK] Updated {count} frontend URL(s): "
            f"{replacement}"
        )


# ------------------------------------------------------------
# Generic literal fallbacks that may exist in JavaScript.
# ------------------------------------------------------------

html = html.replace(
    "/api/supervisor/${SUPERVISOR_ID}/applications",
    "/api/supervisor/applications",
)

html = html.replace(
    "/api/supervisor/${supervisorId}/applications",
    "/api/supervisor/applications",
)

html = html.replace(
    "/api/supervisor/${SUPERVISOR_ID}/engineer/${engineerId}/application",
    "/api/supervisor/engineer/${engineerId}/application",
)

html = html.replace(
    "/api/supervisor/${supervisorId}/engineer/${engineerId}/application",
    "/api/supervisor/engineer/${engineerId}/application",
)


if html == original_html:

    print(
        "[WARNING] No frontend URL changes were detected."
    )

    print(
        "The backend was updated, but supervisor.html "
        "may use different variable names."
    )

else:

    SUPERVISOR_HTML.write_text(
        html,
        encoding="utf-8"
    )

    print("[OK] supervisor.html updated.")


# ============================================================
# VALIDATION
# ============================================================

print()
print("=" * 70)
print("VALIDATION")
print("=" * 70)
print()

verification_text_after = VERIFICATION.read_text(
    encoding="utf-8"
)

# Check canonical routes exist.
required_routes = [
    '@router.get("/api/supervisor/applications")',
    '@router.post("/api/supervisor/applications")',
    '@router.delete(',
    '/api/supervisor/applications/{application_id}',
    '/api/supervisor/engineer/{engineer_id}/application',
    '/api/supervisor/engineer/{engineer_id}/application/{application_id}',
]

for route in required_routes:

    if route in verification_text_after:

        print(f"[OK] Found: {route}")

    else:

        print(f"[ERROR] Missing: {route}")


# ------------------------------------------------------------
# Check old dynamic application routes.
# ------------------------------------------------------------

old_patterns = [
    '/api/supervisor/{supervisor_id}/applications',
    '/api/supervisor/{supervisor_id}/applications/{application_id}',
    '/api/supervisor/{supervisor_id}/engineer/{engineer_id}/application',
    '/api/supervisor/{supervisor_id}/engineer/{engineer_id}/application/{application_id}',
]

print()

for old_pattern in old_patterns:

    if old_pattern in verification_text_after:

        print(
            f"[WARNING] Old route still exists: "
            f"{old_pattern}"
        )

    else:

        print(
            f"[OK] Old route removed: "
            f"{old_pattern}"
        )


# ============================================================
# SUMMARY
# ============================================================

print()
print("=" * 70)
print("FIX COMPLETED")
print("=" * 70)
print()

print("Backups:")
print(f"  {verification_backup}")
print(f"  {supervisor_backup}")

print()
print("Modified:")
print(f"  {VERIFICATION}")
print(f"  {SUPERVISOR_HTML}")

print()
print("Next command:")
print()
print("  python -m py_compile app\\routers\\verification.py")
print()
print("Then start:")
print()
print("  uvicorn app.main:app --reload")
print()
print("=" * 70)