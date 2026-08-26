import sys
import os

# Set working directory to project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal
from app.models.engineer import Engineer
from app.models.applications import Application
from app.models.audit import AuditLog
from app.models.verification import EngineerApplicationAccess
from app.routers.verification import (
    list_supervisor_applications,
    create_application_for_all_engineers,
    remove_application_for_all_engineers,
    remove_application_for_engineer,
    assign_application_to_engineer_by_supervisor,
    add_application_for_engineer,
    ApplicationCreate,
)
from app.routers.portal import supervisor_engineer_details, all_engineers, build_engineer_applications
from fastapi.templating import Jinja2Templates
from fastapi import Request

def run_tests():
    db = SessionLocal()
    try:
        # 1. Fetch Supervisor and Normal Engineer
        sup = db.query(Engineer).filter(Engineer.role == 'SUPERVISOR', Engineer.active == True).first()
        eng = db.query(Engineer).filter(Engineer.role != 'SUPERVISOR', Engineer.active == True).first()

        assert sup is not None, "Supervisor not found in database"
        assert eng is not None, "Engineer not found in database"
        print(f"✓ Found Supervisor: ID {sup.id} ({sup.alias})")
        print(f"✓ Found Engineer: ID {eng.id} ({eng.alias})")

        # 2. Test list_supervisor_applications (both standard and parameterized)
        apps_std = list_supervisor_applications(None, db, sup)
        apps_param = list_supervisor_applications(sup.id, db, sup)
        assert len(apps_std) > 0, "No active applications returned"
        assert len(apps_std) == len(apps_param), "Mismatch between standard and parameterized app list"
        print(f"✓ list_supervisor_applications returned {len(apps_std)} active applications")

        # 3. Test create_application_for_all_engineers
        test_app_name = "Citrix_Test_Suite_App"
        # Cleanup if previously exists
        prev = db.query(Application).filter(Application.name == test_app_name).first()
        if prev:
            db.query(AuditLog).filter(AuditLog.application_id == prev.id).delete()
            db.query(EngineerApplicationAccess).filter(EngineerApplicationAccess.application_id == prev.id).delete()
            db.delete(prev)
            db.commit()

        app_payload = ApplicationCreate(
            name=test_app_name,
            description="Automated Test Citrix Application",
            access_status="Required"
        )
        res_create = create_application_for_all_engineers(app_payload, None, db, sup)
        print(f"✓ create_application_for_all_engineers: {res_create['message']} (Assigned to {res_create['assigned']} engineers)")
        app_id = res_create['application_id']

        # Verify engineer now has this application assigned
        eng_details = supervisor_engineer_details(eng.id, db, sup)
        eng_app_ids = [a['application_id'] for a in eng_details['applications']]
        assert app_id in eng_app_ids, f"App ID {app_id} not found in engineer's assigned applications"
        print(f"✓ Verified app {test_app_name} is assigned to engineer {eng.alias}")

        # 4. Test remove_application_for_engineer (specific delete)
        res_eng_del = remove_application_for_engineer(eng.id, app_id, None, db, sup)
        print(f"✓ remove_application_for_engineer: {res_eng_del['message']}")

        # Verify engineer no longer has this application, but application remains active
        eng_details_after = supervisor_engineer_details(eng.id, db, sup)
        eng_app_ids_after = [a['application_id'] for a in eng_details_after['applications']]
        assert app_id not in eng_app_ids_after, f"App ID {app_id} was not removed from engineer {eng.alias}"
        app_check = db.query(Application).filter(Application.id == app_id).first()
        assert app_check.active == True, "Application should still be active for other engineers"
        print(f"✓ Verified app was removed for {eng.alias} only while remaining active globally")

        # 5. Test assign_application_to_engineer_by_supervisor
        res_assign = assign_application_to_engineer_by_supervisor(eng.id, app_payload, None, db, sup)
        print(f"✓ assign_application_to_engineer_by_supervisor: {res_assign['message']}")

        # 6. Test remove_application_for_all_engineers (global delete)
        res_global_del = remove_application_for_all_engineers(app_id, None, db, sup)
        print(f"✓ remove_application_for_all_engineers: {res_global_del['message']}")
        app_check_inactive = db.query(Application).filter(Application.id == app_id).first()
        assert app_check_inactive.active == False, "Application should be inactive"

        # 7. Test engineer self-adding application
        self_add_name = "Self_Added_Test_App"
        prev_self = db.query(Application).filter(Application.name == self_add_name).first()
        if prev_self:
            db.query(AuditLog).filter(AuditLog.application_id == prev_self.id).delete()
            db.query(EngineerApplicationAccess).filter(EngineerApplicationAccess.application_id == prev_self.id).delete()
            db.delete(prev_self)
            db.commit()

        self_payload = ApplicationCreate(name=self_add_name, access_status="Optional")
        res_self = add_application_for_engineer(eng.id, self_payload, db, eng)
        print(f"✓ add_application_for_engineer (self-service): {res_self['message']}")

        # Cleanup self-added test app
        self_app_rec = db.query(Application).filter(Application.name == self_add_name).first()
        if self_app_rec:
            db.query(AuditLog).filter(AuditLog.application_id == self_app_rec.id).delete()
            db.query(EngineerApplicationAccess).filter(EngineerApplicationAccess.application_id == self_app_rec.id).delete()
            db.delete(self_app_rec)
            db.commit()

        # Cleanup created test app
        if app_check_inactive:
            db.query(AuditLog).filter(AuditLog.application_id == app_check_inactive.id).delete()
            db.query(EngineerApplicationAccess).filter(EngineerApplicationAccess.application_id == app_check_inactive.id).delete()
            db.delete(app_check_inactive)
            db.commit()

        # 8. Test Jinja2 templates rendering
        templates = Jinja2Templates(directory="app/templates")
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": [],
        }
        mock_request = Request(scope)

        # Test supervisor.html render
        sup_html = templates.get_template("supervisor.html").render(
            request=mock_request,
            engineer=sup,
            engineers=all_engineers(db, sup),
            reminder_days=15,
        )
        assert "Application Management" in sup_html
        assert "Request Number" in sup_html
        assert "Requests Completed" in sup_html
        assert "btn-3d" in sup_html
        print("✓ supervisor.html rendered successfully with all required tabs, 3D buttons, and labels")

        # Test verification.html render
        ver_html = templates.get_template("verification.html").render(
            request=mock_request,
            engineer=eng,
            engineer_id=eng.id,
            applications=build_engineer_applications(eng.id, db),
            reminder_days=15,
        )
        assert "Application Access Verification" in ver_html
        assert "Request Number" in ver_html
        assert "Add Application" in ver_html
        assert "btn-3d" in ver_html
        print("✓ verification.html rendered successfully with add application card, 3D buttons, and labels")

        print("\n==========================================")
        print("🎉 ALL BACKEND & TEMPLATE TESTS PASSED! 🎉")
        print("==========================================")

    finally:
        db.close()

if __name__ == '__main__':
    run_tests()
