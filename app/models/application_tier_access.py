from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.database import Base


class ApplicationTierAccess(Base):
    """Defines which engineer tier can receive an application."""

    __tablename__ = "ac_application_tier_access"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, nullable=False, unique=True, index=True)
    display_name = Column(String(200), nullable=False)
    tier1_access = Column(Boolean, nullable=False, default=False)
    tier2_access = Column(Boolean, nullable=False, default=False)
    tier3_access = Column(Boolean, nullable=False, default=False)
    im_above_access = Column(Boolean, nullable=False, default=False)
    active = Column(Boolean, nullable=False, default=True)
    source_label = Column(String(200), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.getdate())
    updated_at = Column(DateTime, nullable=False, server_default=func.getdate())
