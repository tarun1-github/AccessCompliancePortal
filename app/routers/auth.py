from datetime import datetime

from fastapi import (
    APIRouter,
    Depends,
    Form,
    Request,
    Response,
)

from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth import (
    clear_session,
    create_session,
    refresh_session,
    get_current_engineer,
    hash_password,
    verify_password,
)
from app.database import get_db
from app.models.engineer import Engineer


router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)


# ============================================================
# LOGIN PAGE
# ============================================================

@router.get(
    "/login",
    response_class=HTMLResponse,
)
def login_page(
    request: Request,
):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "request": request,
            "first_time": False,
        },
    )


# ============================================================
# LOGIN
#
# EXISTING USER
# ----------------
# Alias + Password
#
# FIRST-TIME USER
# ----------------
# Alias only
# System detects password_hash is NULL
# User gets Set My Password option
# ============================================================

@router.post(
    "/login",
    response_class=HTMLResponse,
)
def login(
    request: Request,

    username: str = Form(...),

    # IMPORTANT:
    # Password is optional because a first-time
    # user does not have a password yet.
    password: str = Form(""),

    db: Session = Depends(get_db),
):

    alias = username.strip().lower()

    # --------------------------------------------------------
    # FIND ENGINEER
    # --------------------------------------------------------

    engineer = (
        db.query(Engineer)
        .filter(
            Engineer.alias == alias,
            Engineer.active == True,
        )
        .first()
    )

    # --------------------------------------------------------
    # USER NOT FOUND
    # --------------------------------------------------------

    if engineer is None:

        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "request": request,
                "error": "Invalid username or password.",
                "username": username,
                "first_time": False,
            },
            status_code=401,
        )

    # --------------------------------------------------------
    # FIRST-TIME USER
    #
    # password_hash = NULL
    # OR
    # must_set_password = True
    #
    # Do NOT ask them for a password.
    # --------------------------------------------------------

    if (
        not engineer.password_hash
        or bool(engineer.must_set_password)
    ):

        # ----------------------------------------------------
        # Password setup requires a setup token.
        # ----------------------------------------------------

        if not engineer.verification_token:

            return templates.TemplateResponse(
                request=request,
                name="login.html",
                context={
                    "request": request,
                    "error": (
                        "Your account is ready for password "
                        "setup, but the setup token is missing. "
                        "Please contact the portal administrator."
                    ),
                    "username": username,
                    "first_time": False,
                },
                status_code=403,
            )

        # ----------------------------------------------------
        # SHOW FIRST-TIME SETUP OPTION
        # ----------------------------------------------------

        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "request": request,
                "username": username,
                "engineer_name": engineer.name,
                "first_time": True,
                "setup_token": engineer.verification_token,
            },
            status_code=200,
        )

    # --------------------------------------------------------
    # EXISTING USER
    #
    # Password is required.
    # --------------------------------------------------------

    if not password:

        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "request": request,
                "error": "Please enter your password.",
                "username": username,
                "first_time": False,
            },
            status_code=400,
        )

    # --------------------------------------------------------
    # VERIFY PASSWORD
    # --------------------------------------------------------

    if not verify_password(
        password,
        engineer.password_hash,
    ):

        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "request": request,
                "error": "Invalid username or password.",
                "username": username,
                "first_time": False,
            },
            status_code=401,
        )

    # --------------------------------------------------------
    # UPDATE LAST LOGIN
    # --------------------------------------------------------

    engineer.last_login_at = datetime.utcnow()

    db.commit()

    # --------------------------------------------------------
    # CREATE SESSION
    # --------------------------------------------------------

    response = RedirectResponse(
        url=f"/{engineer.alias}",
        status_code=303,
    )

    create_session(
        response,
        engineer,
    )

    return response


# ============================================================
# INITIAL PASSWORD SETUP PAGE
#
# URL:
#
# /set-password?token=<verification_token>
# ============================================================

@router.get(
    "/set-password",
    response_class=HTMLResponse,
)
def set_password_page(
    request: Request,

    token: str = "",

    db: Session = Depends(get_db),
):

    token = token.strip()

    # --------------------------------------------------------
    # TOKEN REQUIRED
    # --------------------------------------------------------

    if not token:

        return templates.TemplateResponse(
            request=request,
            name="set_password.html",
            context={
                "request": request,
                "error": (
                    "Password setup link is missing."
                ),
            },
            status_code=400,
        )

    # --------------------------------------------------------
    # FIND ENGINEER USING TOKEN
    # --------------------------------------------------------

    engineer = (
        db.query(Engineer)
        .filter(
            Engineer.verification_token == token,
            Engineer.active == True,
        )
        .first()
    )

    # --------------------------------------------------------
    # INVALID TOKEN
    # --------------------------------------------------------

    if engineer is None:

        return templates.TemplateResponse(
            request=request,
            name="set_password.html",
            context={
                "request": request,
                "error": (
                    "This password setup link is "
                    "invalid or has already been used."
                ),
            },
            status_code=400,
        )

    # --------------------------------------------------------
    # PASSWORD ALREADY SET
    # --------------------------------------------------------

    if engineer.password_hash:

        return templates.TemplateResponse(
            request=request,
            name="set_password.html",
            context={
                "request": request,
                "error": (
                    "A password has already been configured "
                    "for this account. Please use the normal "
                    "login page."
                ),
            },
            status_code=400,
        )

    # --------------------------------------------------------
    # DISPLAY SET PASSWORD PAGE
    # --------------------------------------------------------

    return templates.TemplateResponse(
        request=request,
        name="set_password.html",
        context={
            "request": request,
            "engineer": engineer,
            "token": token,
        },
    )


# ============================================================
# INITIAL PASSWORD SETUP
# ============================================================

@router.post(
    "/set-password",
    response_class=HTMLResponse,
)
def set_password(
    request: Request,

    token: str = Form(...),

    new_password: str = Form(...),

    confirm_password: str = Form(...),

    db: Session = Depends(get_db),
):

    token = token.strip()

    # --------------------------------------------------------
    # VALIDATE TOKEN
    # --------------------------------------------------------

    engineer = (
        db.query(Engineer)
        .filter(
            Engineer.verification_token == token,
            Engineer.active == True,
        )
        .first()
    )

    if engineer is None:

        return templates.TemplateResponse(
            request=request,
            name="set_password.html",
            context={
                "request": request,
                "error": (
                    "This password setup link is "
                    "invalid or has already been used."
                ),
            },
            status_code=400,
        )

    # --------------------------------------------------------
    # PASSWORD ALREADY SET
    # --------------------------------------------------------

    if engineer.password_hash:

        return templates.TemplateResponse(
            request=request,
            name="set_password.html",
            context={
                "request": request,
                "error": (
                    "Password has already been configured."
                ),
            },
            status_code=400,
        )

    # --------------------------------------------------------
    # PASSWORD LENGTH
    # --------------------------------------------------------

    if len(new_password) < 8:

        return templates.TemplateResponse(
            request=request,
            name="set_password.html",
            context={
                "request": request,
                "engineer": engineer,
                "token": token,
                "error": (
                    "Password must be at least 8 characters."
                ),
            },
            status_code=400,
        )

    # --------------------------------------------------------
    # PASSWORD MATCH
    # --------------------------------------------------------

    if new_password != confirm_password:

        return templates.TemplateResponse(
            request=request,
            name="set_password.html",
            context={
                "request": request,
                "engineer": engineer,
                "token": token,
                "error": "Passwords do not match.",
            },
            status_code=400,
        )

    # --------------------------------------------------------
    # SAVE PASSWORD
    # --------------------------------------------------------

    engineer.password_hash = hash_password(
        new_password
    )

    engineer.password_set_at = datetime.utcnow()

    engineer.must_set_password = False

    # --------------------------------------------------------
    # CONSUME ONE-TIME TOKEN
    # --------------------------------------------------------

    engineer.verification_token = None

    engineer.last_login_at = datetime.utcnow()

    db.commit()

    # --------------------------------------------------------
    # AUTOMATIC LOGIN
    # --------------------------------------------------------

    response = RedirectResponse(
        url=f"/{engineer.alias}",
        status_code=303,
    )

    create_session(
        response,
        engineer,
    )

    return response


# ============================================================
# CHANGE PASSWORD PAGE
# ============================================================

@router.get(
    "/change-password",
    response_class=HTMLResponse,
)
def change_password_page(
    request: Request,

    current: Engineer = Depends(
        get_current_engineer
    ),
):

    return templates.TemplateResponse(
        request=request,
        name="change_password.html",
        context={
            "request": request,
            "engineer": current,
        },
    )


# ============================================================
# CHANGE PASSWORD
# ============================================================

@router.post(
    "/change-password",
    response_class=HTMLResponse,
)
def change_password(
    request: Request,

    current_password: str = Form(...),

    new_password: str = Form(...),

    confirm_password: str = Form(...),

    current: Engineer = Depends(
        get_current_engineer
    ),

    db: Session = Depends(get_db),
):

    # --------------------------------------------------------
    # CURRENT PASSWORD
    # --------------------------------------------------------

    if not verify_password(
        current_password,
        current.password_hash,
    ):

        return templates.TemplateResponse(
            request=request,
            name="change_password.html",
            context={
                "request": request,
                "engineer": current,
                "error": (
                    "Current password is incorrect."
                ),
            },
            status_code=400,
        )

    # --------------------------------------------------------
    # NEW PASSWORD LENGTH
    # --------------------------------------------------------

    if len(new_password) < 8:

        return templates.TemplateResponse(
            request=request,
            name="change_password.html",
            context={
                "request": request,
                "engineer": current,
                "error": (
                    "New password must be at least "
                    "8 characters."
                ),
            },
            status_code=400,
        )

    # --------------------------------------------------------
    # NEW PASSWORD MATCH
    # --------------------------------------------------------

    if new_password != confirm_password:

        return templates.TemplateResponse(
            request=request,
            name="change_password.html",
            context={
                "request": request,
                "engineer": current,
                "error": (
                    "New passwords do not match."
                ),
            },
            status_code=400,
        )

    # --------------------------------------------------------
    # SAVE NEW PASSWORD
    # --------------------------------------------------------

    current.password_hash = hash_password(
        new_password
    )

    current.password_set_at = datetime.utcnow()

    current.must_set_password = False

    db.commit()

    # --------------------------------------------------------
    # CREATE FRESH SESSION
    # --------------------------------------------------------

    response = RedirectResponse(
        url=f"/{current.alias}",
        status_code=303,
    )

    create_session(
        response,
        current,
    )

    return response


# ============================================================
# SESSION REFRESH
#
# Browser calls this every 5 minutes.
# ============================================================

@router.post(
    "/session/refresh"
)
def session_refresh(
    response: Response,

    current: Engineer = Depends(
        get_current_engineer
    ),
):

    refresh_session(
        response,
        current,
    )

    return {
        "status": "ok",
        "message": "Session refreshed",
    }


# ============================================================
# LOGOUT
# ============================================================

@router.post("/logout")
def logout():

    response = RedirectResponse(
        url="/login",
        status_code=303,
    )

    clear_session(response)

    return response