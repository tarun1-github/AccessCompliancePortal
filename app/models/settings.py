from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from app.database import Base


class PortalSetting(Base):
    __tablename__ = "ac_portal_settings"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    setting_key = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )

    setting_value = Column(
        String(500),
        nullable=False
    )

    description = Column(
        String(500),
        nullable=True
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now
    )

    updated_by = Column(
        String(255),
        nullable=True
    )