from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.applications import Application

router = APIRouter()


@router.get("/applications")
def get_applications(db: Session = Depends(get_db)):

    applications = (
        db.query(Application)
        .filter(Application.active == True)
        .order_by(Application.id)
        .all()
    )

    return [
        {
            "id": a.id,
            "name": a.name,
            "description": a.description,
            "active": a.active
        }
        for a in applications
    ]