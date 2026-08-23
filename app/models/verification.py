from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from app.database import Base


class EngineerApplicationAccess(Base):
    __tablename__ = "ac_engineer_application_access"

    id = Column(Integer, primary_key=True, index=True)
    engineer_id = Column(Integer, nullable=False, index=True)
    application_id = Column(Integer, nullable=False, index=True)

    access_status = Column(String(50), nullable=False)
    verification_status = Column(
        String(50), nullable=False, default="Pending"
    )

    last_verified_date = Column(DateTime, nullable=True)
    remarks = Column(String(200), nullable=True)

    # ARM
    arm_ticket = Column(String(100), nullable=True)
    ticket_status = Column(
        String(30), nullable=False, default="Request Not Initiated"
    )

    # Reminder / email tracking
    next_reminder_date = Column(DateTime, nullable=True, index=True)
    last_email_sent_at = Column(DateTime, nullable=True)
    email_count = Column(Integer, nullable=False, default=0)

    # Audit / update timestamp
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now,
    )
