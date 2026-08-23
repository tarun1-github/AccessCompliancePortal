from sqlalchemy import Boolean, Column, Integer, String

from app.database import Base


class Engineer(Base):

    __tablename__ = "ac_engineers"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    name = Column(
        String(200),
        nullable=False,
    )

    email = Column(
        String(255),
        nullable=True,
    )

    level = Column(
        String(50),
        nullable=True,
    )

    rm_email = Column(
        String(255),
        nullable=True,
    )

    alias = Column(
        String(100),
        nullable=True,
        unique=True,
        index=True,
    )

    role = Column(
        String(50),
        nullable=False,
        default="ENGINEER",
    )

    supervisor_id = Column(
        Integer,
        nullable=True,
        index=True,
    )

    active = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    verification_token = Column(
        String(255),
        nullable=True,
        unique=True,
        index=True,
    )