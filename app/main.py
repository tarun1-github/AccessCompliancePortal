from fastapi import FastAPI

from app.database import Base, engine

# Import models so SQLAlchemy knows about all tables
from app.models.engineer import Engineer
from app.models.applications import Application
from app.models.verification import EngineerApplicationAccess
from app.models.audit import AuditLog
from app.models.application_tier_access import ApplicationTierAccess

# Import routers
from app.routers import auth
from app.routers import verification
from app.routers import portal
from app.routers import engineer_management
from app.routers import application_mapping


app = FastAPI(
    title="CMS BOA EV Access Compliance Portal",
    version="2.0.0",
)


@app.on_event("startup")
def startup_event():

    Base.metadata.create_all(
        bind=engine
    )


@app.get("/health")
def health_check():

    return {
        "status": "ok",
        "application": (
            "CMS BOA EV Access Compliance Portal"
        ),
    }


# IMPORTANT:
# auth + verification + engineer_management
# must be registered before portal because
# portal contains /{alias} catch-all routing.

app.include_router(
    auth.router
)

app.include_router(
    verification.router
)

app.include_router(
    engineer_management.router
)

# Application mapping APIs must be registered before portal.
# They use the DB-driven engineer/tier/application matrix.
app.include_router(
    application_mapping.router
)

app.include_router(
    portal.router
)
