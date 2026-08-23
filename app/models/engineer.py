from sqlalchemy import Boolean, Column, DateTime, Integer, String

from app.database import Base


class Engineer(Base):
    __tablename__ = "ac_engineers"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(200), nullable=False)
    email = Column(String(255), nullable=True)
    level = Column(String(50), nullable=True)
    rm_email = Column(String(255), nullable=True)

    alias = Column(String(100), nullable=True, unique=True, index=True)
    role = Column(String(50), nullable=False, default="ENGINEER")
    supervisor_id = Column(Integer, nullable=True, index=True)

    active = Column(Boolean, nullable=False, default=True)

    verification_token = Column(
        String(255),
        nullable=True,
        unique=True,
        index=True,
    )

    # Phase 2A - local authentication

    password_hash = Column(
    String(255),
    nullable=True,
)

    password_set_at = Column(
    DateTime,
    nullable=True,
)

    must_set_password = Column(
    Boolean,
    nullable=False,
    default=True,
)

    last_login_at = Column(
    DateTime,
    nullable=True,
)

# Phase 2B - forgot password

    password_reset_token = Column(
    String(255),
    nullable=True,
    unique=True,
    index=True,
)

    password_reset_expires_at = Column(
    DateTime,
    nullable=True,
)