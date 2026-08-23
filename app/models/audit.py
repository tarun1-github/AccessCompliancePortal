from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Integer,
    String
)
from sqlalchemy.sql import func

from app.database import Base


class AuditLog(Base):

    __tablename__ = "ac_audit_log"


    # ========================================================
    # PRIMARY KEY
    # ========================================================

    id = Column(
        BigInteger,
        primary_key=True,
        index=True
    )


    # ========================================================
    # RELATED RECORDS
    # ========================================================

    engineer_id = Column(
        Integer,
        nullable=True,
        index=True
    )

    application_id = Column(
        Integer,
        nullable=True,
        index=True
    )


    # ========================================================
    # CHANGE DETAILS
    # ========================================================

    action = Column(
        String(100),
        nullable=False,
        index=True
    )

    old_status = Column(
        String(50),
        nullable=True
    )

    new_status = Column(
        String(50),
        nullable=True
    )

    remarks = Column(
        String(2000),
        nullable=True
    )


    # ========================================================
    # WHO MADE THE CHANGE
    # ========================================================

    performed_by = Column(
        String(200),
        nullable=True
    )

    performed_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now()
    )