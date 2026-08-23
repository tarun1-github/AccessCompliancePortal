from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Integer,
    String,
    Text,
)
from sqlalchemy.sql import func

from app.database import Base


class NotificationLog(Base):

    __tablename__ = "ac_notification_log"

    id = Column(
        BigInteger,
        primary_key=True,
        index=True
    )

    engineer_id = Column(
        Integer,
        nullable=False,
        index=True
    )

    access_id = Column(
        Integer,
        nullable=True,
        index=True
    )

    notification_type = Column(
        String(30),
        nullable=False,
        index=True
    )

    recipient_email = Column(
        String(255),
        nullable=False
    )

    cc_email = Column(
        String(255),
        nullable=True
    )

    subject = Column(
        String(500),
        nullable=True
    )

    sent_at = Column(
        DateTime,
        nullable=True
    )

    status = Column(
        String(20),
        nullable=False,
        index=True
    )

    error_message = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now()
    )