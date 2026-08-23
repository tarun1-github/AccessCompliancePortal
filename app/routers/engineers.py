from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.engineer import Engineer

router = APIRouter()


@router.get("/engineers")
def get_engineers(db: Session = Depends(get_db)):

    engineers = (
        db.query(Engineer)
        .filter(Engineer.active == True)
        .order_by(Engineer.name)
        .all()
    )

    return [
        {
            "id": e.id,
            "name": e.name,
            "email": e.email,
            "level": e.level,
            "rm_email": e.rm_email,
            "active": e.active
        }
        for e in engineers
    ]