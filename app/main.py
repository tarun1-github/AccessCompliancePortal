from fastapi import FastAPI

from app.database import Base, engine

# Import models so SQLAlchemy knows about all tables
from app.models.engineer import Engineer
from app.models.applications import Application
from app.models.verification import EngineerApplicationAccess
from app.models.audit import AuditLog

# Import routers
from app.routers import portal
from app.routers import verification


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="CMS BOA EV Access Compliance Portal",
    version="2.0.0",
)


# ============================================================
# CREATE DATABASE TABLES
# ============================================================

@app.on_event("startup")
def startup_event():

    Base.metadata.create_all(
        bind=engine
    )


# ============================================================
# INCLUDE ROUTERS
# ============================================================

app.include_router(
    portal.router
)

app.include_router(
    verification.router
)


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health_check():

    return {
        "status": "ok",
        "application": "CMS BOA EV Access Compliance Portal",
    }