from sqlalchemy import Column, Integer, String, Boolean
from app.database import Base


class Application(Base):
    __tablename__ = "ac_applications"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(String(500), nullable=True)
    active = Column(Boolean, default=True)