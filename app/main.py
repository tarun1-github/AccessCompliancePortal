from fastapi import FastAPI

from app.database import Base, engine

# Import models so SQLAlchemy knows about all tables
from app.models.engineer import Engineer
from app.models.applications import Application
from app.models.verification import EngineerApplicationAccess
from app.models.audit import AuditLog

# Import routers
from app.routers import auth
from app.routers import verification
from app.routers import portal


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
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "application": "CMS BOA EV Access Compliance Portal",
    }


# ============================================================
# INCLUDE ROUTERS
#
# IMPORTANT:
# auth.router and verification.router MUST come before portal.router.
#
# portal.py contains:
#
#     /{alias}
#
# which is a catch-all route and would otherwise capture
# /login before auth.router gets a chance to handle it.
# ============================================================

app.include_router(
    auth.router
)

app.include_router(
    verification.router
)

app.include_router(
    portal.router
)