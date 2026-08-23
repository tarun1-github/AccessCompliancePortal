# Phase 2A installation

## 1. Copy files

Copy:
- app/auth.py
- app/routers/auth.py
- app/models/engineer.py
- app/templates/login.html
- app/templates/set_password.html
- app/templates/change_password.html

Do NOT overwrite unrelated files.

## 2. Update app/main.py

Add:
    from app.routers import auth

Then add:
    app.include_router(auth.router)

## 3. Update app/routers/portal.py

Authentication must be enforced on the page and API routes.

Import:
    from app.auth import get_current_engineer, require_supervisor, require_own_engineer

For the engineer page route that serves /{alias}, resolve the alias and require:
    current = Depends(get_current_engineer)

Then reject if current.id != target.id with HTTP 403.

For:
    /api/engineer/{engineer_id}
    /engineers/{engineer_id}/access
    /verification/{engineer_id}/{application_id}
use require_own_engineer or current-user checks.

For supervisor endpoints:
    /api/supervisor/engineers
    /api/supervisor/engineer/{engineer_id}
    /api/dashboard
    /analytics/*
use require_supervisor.

The important rule is: do not rely on the URL alias alone. Every backend API must validate the authenticated engineer.

## 4. Update app/routers/verification.py

Import:
    from app.auth import get_current_engineer, require_own_engineer, require_supervisor

Add the dependency to normal engineer GET/PATCH routes and verify the authenticated engineer owns engineer_id.

Add require_supervisor to ARM/supervisor routes.

## 5. Database

Run database/deployment/06_auth_migration.sql against CPDB.

## 6. .env

Add AUTH_SECRET_KEY=<long random secret>.

Never commit the real .env.

## 7. First-time password

All existing engineers will have:
    password_hash = NULL
    must_set_password = 1

That means the existing alias/password cannot be used yet. For the first login flow, the application needs a secure bootstrap mechanism. Do NOT simply let anyone who knows an alias create its password.

Recommended LAB bootstrap:
- supervisor/admin sets a temporary one-time password or setup token for each engineer
- engineer logs in once and changes it

The current package deliberately does NOT implement an insecure "alias only can create password" flow.

## 8. Important

The supplied Phase 2A code is the authentication foundation. Before enabling it on the LAB server, apply the authorization dependencies to every existing portal/verification/analytics API route. Hiding links or changing HTML is not security.
