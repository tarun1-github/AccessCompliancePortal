from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.notification import NotificationLog


router = APIRouter(
    prefix="/api/notifications",
    tags=["Notifications"],
)


@router.get("/")
def get_notifications(
    db: Session = Depends(get_db),
):
    notifications = (
        db.query(NotificationLog)
        .order_by(
            NotificationLog.created_at.desc()
        )
        .all()
    )

    return [
        {
            "id": notification.id,
            "engineer_id": notification.engineer_id,
            "access_id": notification.access_id,
            "notification_type": notification.notification_type,
            "recipient_email": notification.recipient_email,
            "cc_email": notification.cc_email,
            "subject": notification.subject,
            "sent_at": (
                notification.sent_at.isoformat()
                if notification.sent_at
                else None
            ),
            "status": notification.status,
            "error_message": notification.error_message,
            "created_at": (
                notification.created_at.isoformat()
                if notification.created_at
                else None
            ),
        }
        for notification in notifications
    ]