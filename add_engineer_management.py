from pathlib import Path
import shutil
from datetime import datetime
import ast

ROOT = Path(__file__).resolve().parent
VERIFICATION = ROOT / "app" / "routers" / "verification.py"
SUPERVISOR_HTML = ROOT / "app" / "templates" / "supervisor.html"

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
VERIFICATION_BACKUP = ROOT / f"verification.py.before_engineer_management_{stamp}"
HTML_BACKUP = ROOT / f"supervisor.html.before_engineer_management_{stamp}"

BACKEND_MARKER = "# ACCESS PORTAL ENGINEER MANAGEMENT - GENERATED BLOCK"
FRONTEND_MARKER = "ACCESS PORTAL ENGINEER MANAGEMENT - GENERATED UI"

BACKEND = r'''# ACCESS PORTAL ENGINEER MANAGEMENT - GENERATED BLOCK

class EngineerManagementCreate(BaseModel):
    alias: str
    name: str
    email: Optional[str] = None
    level: Optional[str] = None
    rm_email: Optional[str] = None
    role: str = "ENGINEER"


class EngineerManagementUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    level: Optional[str] = None
    rm_email: Optional[str] = None
    role: Optional[str] = None


def _engineer_management_role(value: Optional[str]) -> str:
    role = (value or "ENGINEER").strip().upper()
    if role not in {"ENGINEER", "SUPERVISOR"}:
        raise HTTPException(status_code=400, detail="Role must be ENGINEER or SUPERVISOR.")
    return role


def _restore_active_applications_for_engineer(db: Session, engineer_id: int) -> int:
    applications = db.query(Application).filter(Application.active == True).all()
    existing = (
        db.query(EngineerApplicationAccess)
        .filter(EngineerApplicationAccess.engineer_id == engineer_id)
        .all()
    )
    existing_ids = {row.application_id for row in existing}
    added = 0

    for application in applications:
        if application.id in existing_ids:
            continue
        db.add(
            EngineerApplicationAccess(
                engineer_id=engineer_id,
                application_id=application.id,
                access_status="Required",
                verification_status="Pending",
                ticket_status=DEFAULT_ARM_STATUS,
            )
        )
        added += 1

    return added


@router.get("/api/supervisor/manage-engineers")
def manage_engineers_list(
    db: Session = Depends(get_db),
    current_user: Engineer = Depends(require_supervisor),
):
    engineers = db.query(Engineer).order_by(Engineer.active.desc(), Engineer.name).all()
    result = []

    for engineer in engineers:
        application_count = (
            db.query(EngineerApplicationAccess)
            .filter(EngineerApplicationAccess.engineer_id == engineer.id)
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


@router.post("/api/supervisor/manage-engineers")
def manage_engineer_create(
    data: EngineerManagementCreate,
    db: Session = Depends(get_db),
    current_user: Engineer = Depends(require_supervisor),
):
    alias = data.alias.strip()
    name = data.name.strip()
    role = _engineer_management_role(data.role)

    if not alias:
        raise HTTPException(status_code=400, detail="Alias is required.")
    if not name:
        raise HTTPException(status_code=400, detail="Name is required.")

    existing = db.query(Engineer).filter(Engineer.alias.ilike(alias)).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Engineer alias '{alias}' already exists.")

    engineer = Engineer(
        alias=alias,
        name=name,
        email=data.email.strip() if data.email and data.email.strip() else None,
        level=data.level.strip() if data.level and data.level.strip() else None,
        rm_email=data.rm_email.strip() if data.rm_email and data.rm_email.strip() else None,
        role=role,
        active=True,
        must_set_password=True,
    )

    db.add(engineer)
    db.flush()

    assigned = _restore_active_applications_for_engineer(db, engineer.id)
    performed_by = current_user.alias or current_user.email or current_user.name

    create_audit_entry(
        db,
        engineer.id,
        None,
        "ENGINEER_CREATED",
        None,
        role,
        f"Created {role.lower()} '{alias}'. {assigned} active applications assigned.",
        performed_by,
    )

    try:
        db.commit()
        db.refresh(engineer)
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Unable to create engineer: {exc}")

    return {
        "message": f"{role.title()} '{name}' created successfully.",
        "applications_assigned": assigned,
        "engineer_id": engineer.id,
    }


@router.patch("/api/supervisor/manage-engineers/{engineer_id}")
def manage_engineer_update(
    engineer_id: int,
    data: EngineerManagementUpdate,
    db: Session = Depends(get_db),
    current_user: Engineer = Depends(require_supervisor),
):
    engineer = db.query(Engineer).filter(Engineer.id == engineer_id).first()
    if not engineer:
        raise HTTPException(status_code=404, detail="Engineer not found.")

    old_role = engineer.role

    if data.name is not None:
        name = data.name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="Name cannot be empty.")
        engineer.name = name
    if data.email is not None:
        engineer.email = data.email.strip() or None
    if data.level is not None:
        engineer.level = data.level.strip() or None
    if data.rm_email is not None:
        engineer.rm_email = data.rm_email.strip() or None
    if data.role is not None:
        engineer.role = _engineer_management_role(data.role)

    restored = _restore_active_applications_for_engineer(db, engineer.id) if engineer.active else 0
    performed_by = current_user.alias or current_user.email or current_user.name

    create_audit_entry(
        db,
        engineer.id,
        None,
        "ENGINEER_UPDATED",
        old_role,
        engineer.role,
        f"Updated engineer '{engineer.alias}'. {restored} missing active applications restored.",
        performed_by,
    )

    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Unable to update engineer: {exc}")

    return {"message": f"Engineer '{engineer.name}' updated successfully.", "applications_restored": restored}


@router.delete("/api/supervisor/manage-engineers/{engineer_id}")
def manage_engineer_deactivate(
    engineer_id: int,
    db: Session = Depends(get_db),
    current_user: Engineer = Depends(require_supervisor),
):
    if current_user.id == engineer_id:
        raise HTTPException(status_code=400, detail="You cannot deactivate your own supervisor account.")

    engineer = db.query(Engineer).filter(Engineer.id == engineer_id).first()
    if not engineer:
        raise HTTPException(status_code=404, detail="Engineer not found.")
    if not engineer.active:
        return {"message": f"Engineer '{engineer.name}' is already inactive."}

    engineer.active = False
    performed_by = current_user.alias or current_user.email or current_user.name

    create_audit_entry(
        db,
        engineer.id,
        None,
        "ENGINEER_DEACTIVATED",
        "Active",
        "Inactive",
        f"Deactivated engineer '{engineer.alias}'. Historical records retained.",
        performed_by,
    )

    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Unable to deactivate engineer: {exc}")

    return {"message": f"Engineer '{engineer.name}' deactivated successfully."}


@router.post("/api/supervisor/manage-engineers/{engineer_id}/reactivate")
def manage_engineer_reactivate(
    engineer_id: int,
    db: Session = Depends(get_db),
    current_user: Engineer = Depends(require_supervisor),
):
    engineer = db.query(Engineer).filter(Engineer.id == engineer_id).first()
    if not engineer:
        raise HTTPException(status_code=404, detail="Engineer not found.")

    engineer.active = True
    restored = _restore_active_applications_for_engineer(db, engineer.id)
    performed_by = current_user.alias or current_user.email or current_user.name

    create_audit_entry(
        db,
        engineer.id,
        None,
        "ENGINEER_REACTIVATED",
        "Inactive",
        "Active",
        f"Reactivated engineer '{engineer.alias}'. {restored} applications restored.",
        performed_by,
    )

    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Unable to reactivate engineer: {exc}")

    return {
        "message": f"Engineer '{engineer.name}' reactivated successfully.",
        "applications_restored": restored,
    }

# END ACCESS PORTAL ENGINEER MANAGEMENT - GENERATED BLOCK
'''

FRONTEND = r'''/* ACCESS PORTAL ENGINEER MANAGEMENT - GENERATED UI */
(function () {
    "use strict";

    function esc(value) {
        if (value === null || value === undefined) return "";
        return String(value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    async function loadEngineers() {
        var body = document.getElementById("accessPortalEngineerTableBody");
        if (!body) return;

        body.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:20px;">Loading...</td></tr>';

        try {
            var response = await fetch("/api/supervisor/manage-engineers", { credentials: "same-origin" });
            var data = await response.json().catch(function () { return {}; });
            if (!response.ok) throw new Error(data.detail || "Unable to load engineers.");

            if (!data.length) {
                body.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:20px;">No engineers found.</td></tr>';
                return;
            }

            body.innerHTML = data.map(function (engineer) {
                var status = engineer.active
                    ? '<span style="color:#15803d;font-weight:700;">● Active</span>'
                    : '<span style="color:#b91c1c;font-weight:700;">● Inactive</span>';
                var action = engineer.active
                    ? '<button type="button" onclick="window.accessPortalDeactivateEngineer(' + engineer.id + ')">🔴 Deactivate</button>'
                    : '<button type="button" onclick="window.accessPortalReactivateEngineer(' + engineer.id + ')">🟢 Reactivate</button>';

                return '<tr>' +
                    '<td>' + esc(engineer.alias) + '</td>' +
                    '<td>' + esc(engineer.name) + '</td>' +
                    '<td>' + esc(engineer.email || '') + '</td>' +
                    '<td>' + esc(engineer.role || 'ENGINEER') + '</td>' +
                    '<td>' + (engineer.application_count || 0) + '</td>' +
                    '<td>' + status + '</td>' +
                    '<td><button type="button" onclick="window.accessPortalEditEngineer(' + engineer.id + ')">✏️ Edit</button> ' + action + '</td>' +
                    '</tr>';
            }).join("");
        } catch (error) {
            body.innerHTML = '<tr><td colspan="7" style="color:#b91c1c;text-align:center;padding:20px;">' + esc(error.message) + '</td></tr>';
        }
    }

    function openForm(engineer) {
        document.getElementById("accessPortalEngineerForm").style.display = "block";
        document.getElementById("accessPortalEngineerFormTitle").textContent = engineer ? "Edit Engineer" : "Add Engineer";
        document.getElementById("accessPortalEngineerId").value = engineer ? engineer.id : "";
        document.getElementById("accessPortalEngineerAlias").value = engineer ? engineer.alias : "";
        document.getElementById("accessPortalEngineerName").value = engineer ? engineer.name : "";
        document.getElementById("accessPortalEngineerEmail").value = engineer ? (engineer.email || "") : "";
        document.getElementById("accessPortalEngineerLevel").value = engineer ? (engineer.level || "") : "";
        document.getElementById("accessPortalEngineerRmEmail").value = engineer ? (engineer.rm_email || "") : "";
        document.getElementById("accessPortalEngineerRole").value = engineer ? (engineer.role || "ENGINEER") : "ENGINEER";
        document.getElementById("accessPortalEngineerAlias").disabled = !!engineer;
    }

    function closeForm() {
        document.getElementById("accessPortalEngineerForm").style.display = "none";
    }

    async function editEngineer(id) {
        try {
            var response = await fetch("/api/supervisor/manage-engineers", { credentials: "same-origin" });
            var data = await response.json();
            var engineer = data.find(function (item) { return item.id === id; });
            if (!engineer) throw new Error("Engineer not found.");
            openForm(engineer);
        } catch (error) {
            alert(error.message);
        }
    }

    async function saveEngineer() {
        var id = document.getElementById("accessPortalEngineerId").value;
        var payload = {
            name: document.getElementById("accessPortalEngineerName").value.trim(),
            email: document.getElementById("accessPortalEngineerEmail").value.trim(),
            level: document.getElementById("accessPortalEngineerLevel").value.trim(),
            rm_email: document.getElementById("accessPortalEngineerRmEmail").value.trim(),
            role: document.getElementById("accessPortalEngineerRole").value
        };

        if (!payload.name) {
            alert("Name is required.");
            return;
        }

        var url = id ? "/api/supervisor/manage-engineers/" + id : "/api/supervisor/manage-engineers";
        var method = id ? "PATCH" : "POST";

        if (!id) {
            payload.alias = document.getElementById("accessPortalEngineerAlias").value.trim();
            if (!payload.alias) {
                alert("Alias is required.");
                return;
            }
        }

        try {
            var response = await fetch(url, {
                method: method,
                credentials: "same-origin",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            var data = await response.json().catch(function () { return {}; });
            if (!response.ok) throw new Error(data.detail || "Unable to save engineer.");
            alert(data.message);
            closeForm();
            await loadEngineers();
        } catch (error) {
            alert(error.message);
        }
    }

    async function deactivateEngineer(id) {
        if (!confirm("Deactivate this engineer? Historical access and audit data will be retained.")) return;
        try {
            var response = await fetch("/api/supervisor/manage-engineers/" + id, {
                method: "DELETE",
                credentials: "same-origin"
            });
            var data = await response.json().catch(function () { return {}; });
            if (!response.ok) throw new Error(data.detail || "Unable to deactivate engineer.");
            alert(data.message);
            await loadEngineers();
        } catch (error) {
            alert(error.message);
        }
    }

    async function reactivateEngineer(id) {
        if (!confirm("Reactivate this engineer and restore missing active applications?")) return;
        try {
            var response = await fetch("/api/supervisor/manage-engineers/" + id + "/reactivate", {
                method: "POST",
                credentials: "same-origin"
            });
            var data = await response.json().catch(function () { return {}; });
            if (!response.ok) throw new Error(data.detail || "Unable to reactivate engineer.");
            alert(data.message + "\nApplications restored: " + (data.applications_restored || 0));
            await loadEngineers();
        } catch (error) {
            alert(error.message);
        }
    }

    function install() {
        if (document.getElementById("accessPortalEngineerManagement")) {
            loadEngineers();
            return;
        }

        var container = document.createElement("div");
        container.id = "accessPortalEngineerManagement";
        container.style.cssText = "margin:24px 0;padding:20px;background:#f8fafc;border:1px solid #cbd5e1;border-radius:12px;";
        container.innerHTML =
            '<div style="display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap;">' +
            '<div><h3 style="margin:0;color:#1e3a8a;">👥 Engineer Management</h3><div style="font-size:12px;color:#64748b;margin-top:4px;">Add, edit, deactivate and reactivate engineers and supervisors.</div></div>' +
            '<button type="button" onclick="window.accessPortalOpenEngineerForm(null)">➕ Add Engineer</button>' +
            '</div>' +
            '<div id="accessPortalEngineerForm" style="display:none;margin:18px 0;padding:16px;background:white;border:1px solid #cbd5e1;border-radius:10px;">' +
            '<h4 id="accessPortalEngineerFormTitle">Add Engineer</h4>' +
            '<input type="hidden" id="accessPortalEngineerId">' +
            '<div style="display:grid;grid-template-columns:repeat(2,minmax(200px,1fr));gap:12px;">' +
            '<label>Alias *<input id="accessPortalEngineerAlias" style="width:100%;"></label>' +
            '<label>Name *<input id="accessPortalEngineerName" style="width:100%;"></label>' +
            '<label>Email<input id="accessPortalEngineerEmail" style="width:100%;"></label>' +
            '<label>Level<input id="accessPortalEngineerLevel" style="width:100%;"></label>' +
            '<label>RM Email<input id="accessPortalEngineerRmEmail" style="width:100%;"></label>' +
            '<label>Role<select id="accessPortalEngineerRole" style="width:100%;"><option value="ENGINEER">ENGINEER</option><option value="SUPERVISOR">SUPERVISOR</option></select></label>' +
            '</div>' +
            '<div style="margin-top:14px;"><button type="button" onclick="window.accessPortalSaveEngineer()">💾 Save</button> <button type="button" onclick="window.accessPortalCloseEngineerForm()">Cancel</button></div>' +
            '</div>' +
            '<div style="overflow:auto;margin-top:18px;">' +
            '<table style="width:100%;border-collapse:collapse;">' +
            '<thead><tr><th>Alias</th><th>Name</th><th>Email</th><th>Role</th><th>Applications</th><th>Status</th><th>Actions</th></tr></thead>' +
            '<tbody id="accessPortalEngineerTableBody"></tbody></table></div>';

        var headings = document.querySelectorAll("h1,h2,h3");
        var inserted = false;
        for (var i = 0; i < headings.length; i += 1) {
            var text = (headings[i].textContent || "").toLowerCase();
            if (text.indexOf("application management") !== -1) {
                headings[i].parentElement.insertAdjacentElement("afterend", container);
                inserted = true;
                break;
            }
        }
        if (!inserted) {
            (document.querySelector("main") || document.body).appendChild(container);
        }
        loadEngineers();
    }

    window.accessPortalOpenEngineerForm = openForm;
    window.accessPortalCloseEngineerForm = closeForm;
    window.accessPortalEditEngineer = editEngineer;
    window.accessPortalSaveEngineer = saveEngineer;
    window.accessPortalDeactivateEngineer = deactivateEngineer;
    window.accessPortalReactivateEngineer = reactivateEngineer;

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", install);
    } else {
        install();
    }
}());
/* END ACCESS PORTAL ENGINEER MANAGEMENT - GENERATED UI */
'''


def validate_python(path: Path):
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def main():
    print("=" * 70)
    print("ACCESS COMPLIANCE PORTAL - ENGINEER MANAGEMENT FIX")
    print("=" * 70)

    if not VERIFICATION.exists():
        raise FileNotFoundError(VERIFICATION)
    if not SUPERVISOR_HTML.exists():
        raise FileNotFoundError(SUPERVISOR_HTML)

    shutil.copy2(VERIFICATION, VERIFICATION_BACKUP)
    shutil.copy2(SUPERVISOR_HTML, HTML_BACKUP)
    print(f"[OK] Backup: {VERIFICATION_BACKUP.name}")
    print(f"[OK] Backup: {HTML_BACKUP.name}")

    verification_text = VERIFICATION.read_text(encoding="utf-8")
    if BACKEND_MARKER not in verification_text:
        VERIFICATION.write_text(
            verification_text.rstrip() + "\n\n" + BACKEND.strip() + "\n",
            encoding="utf-8",
        )
        print("[OK] Engineer-management backend added.")
    else:
        print("[INFO] Engineer-management backend already present; skipped.")

    validate_python(VERIFICATION)
    print("[OK] verification.py syntax is valid.")

    html = SUPERVISOR_HTML.read_text(encoding="utf-8")
    if FRONTEND_MARKER not in html:
        lower = html.lower()
        index = lower.rfind("</body>")
        if index == -1:
            raise RuntimeError("Could not find </body> in supervisor.html")
        html = html[:index] + "\n<script>\n" + FRONTEND.strip() + "\n</script>\n" + html[index:]
        SUPERVISOR_HTML.write_text(html, encoding="utf-8")
        print("[OK] Engineer-management UI added.")
    else:
        print("[INFO] Engineer-management UI already present; skipped.")

    print()
    print("=" * 70)
    print("COMPLETE")
    print("=" * 70)
    print("Run:")
    print(r"  python -m py_compile app\routers\verification.py")
    print("Then restart the portal and test Engineer Management.")


if __name__ == "__main__":
    main()
