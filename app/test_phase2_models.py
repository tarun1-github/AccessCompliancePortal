from sqlalchemy import text

from app.database import engine
from app.models.verification import EngineerApplicationAccess
from app.models.settings import PortalSetting
from app.models.notification import NotificationLog
from app.models.audit import AuditLog


print("Testing SQL Server connection...")

with engine.connect() as connection:
    result = connection.execute(
        text("SELECT DB_NAME() AS database_name")
    )

    print("Connected database:", result.scalar())

    result = connection.execute(
        text(
            """
            SELECT COUNT(*)
            FROM dbo.ac_engineer_application_access
            """
        )
    )

    print("Access records:", result.scalar())

    result = connection.execute(
        text(
            """
            SELECT setting_value
            FROM dbo.ac_portal_settings
            WHERE setting_key = 'reminder_days'
            """
        )
    )

    print("Reminder days:", result.scalar())


print()
print("All Phase 2 database models imported successfully.")