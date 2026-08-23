from datetime import datetime

from fastapi import (
    APIRouter,
    Depends,
    Form,
    Request,
    Response,
)

from fastapi.responses import (
    HTMLResponse,
    RedirectResponse,
)

from fastapi.templating import (
    Jinja2Templates,
)

from sqlalchemy.orm import Session

from app.auth import (
    clear_session,
    create_password_reset_token,
    create_session,
    get_current_engineer,
    hash_password,
    password_reset_expiry,
    refresh_session,
    verify_password,
)

from app.database import get_db

from app.models.engineer import Engineer


# ============================================================
# ROUTER / TEMPLATES
# ============================================================

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

    reset_success = (
        request.query_params.get("reset")
        == "success"
    )

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "request": request,

            "reset_success":
                reset_success,
        },
    )


# ============================================================
# LOGIN
# ============================================================

@router.post(
    "/login",
    response_class=HTMLResponse,
)
def login(
    request: Request,

    username: str = Form(...),

    password: str = Form(...),

    db: Session = Depends(
        get_db
    ),
):

    alias = username.strip().lower()

    engineer = (
        db.query(Engineer)
        .filter(
            Engineer.alias == alias,
            Engineer.active == True,
        )
        .first()
    )


    # ========================================================
    # USER NOT FOUND
    # ========================================================

    if engineer is None:

        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "request": request,

                "error":
                    "Invalid username or password.",

                "username":
                    username,
            },

            status_code=401,
        )


    # ========================================================
    # FIRST-TIME USER
    #
    # Password has not been configured yet.
    #
    # The existing verification_token is used for the
    # initial password setup.
    # ========================================================

    if (
        not engineer.password_hash
        or bool(
            engineer.must_set_password
        )
    ):

        if not engineer.verification_token:

            return templates.TemplateResponse(
                request=request,
                name="login.html",
                context={
                    "request": request,

                    "error": (
                        "Password setup is not available "
                        "for this account. Please contact "
                        "the portal administrator."
                    ),

                    "username":
                        username,
                },

                status_code=403,
            )


        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "request": request,

                "error": (
                    "This is your first login. "
                    "Please set your password first."
                ),

                "username":
                    username,

                "first_time":
                    True,

                "setup_token":
                    engineer.verification_token,
            },

            status_code=200,
        )


    # ========================================================
    # NORMAL PASSWORD AUTHENTICATION
    # ========================================================

    if not verify_password(
        password,
        engineer.password_hash,
    ):

        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "request": request,

                "error":
                    "Invalid username or password.",

                "username":
                    username,
            },

            status_code=401,
        )


    # ========================================================
    # UPDATE LAST LOGIN
    # ========================================================

    engineer.last_login_at = datetime.utcnow()

    db.commit()


    # ========================================================
    # CREATE SESSION
    #
    # Session is initially valid for 1 hour.
    # Browser refreshes it every 5 minutes.
    # ========================================================

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
#
# This is only for first-time users.
# ============================================================

@router.get(
    "/set-password",
    response_class=HTMLResponse,
)
def set_password_page(
    request: Request,

    token: str = "",

    db: Session = Depends(
        get_db
    ),
):

    token = token.strip()


    # ========================================================
    # TOKEN MISSING
    # ========================================================

    if not token:

        return templates.TemplateResponse(
            request=request,
            name="set_password.html",
            context={
                "request": request,

                "error":
                    "Password setup link is missing.",
            },

            status_code=400,
        )


    # ========================================================
    # FIND ENGINEER
    # ========================================================

    engineer = (
        db.query(Engineer)
        .filter(
            Engineer.verification_token
            == token,

            Engineer.active
            == True,
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


    # ========================================================
    # PASSWORD ALREADY SET
    # ========================================================

    if engineer.password_hash:

        return templates.TemplateResponse(
            request=request,
            name="set_password.html",
            context={
                "request": request,

                "error": (
                    "A password has already been "
                    "configured for this account. "
                    "Please use the normal login."
                ),
            },

            status_code=400,
        )


    # ========================================================
    # DISPLAY PASSWORD SETUP PAGE
    # ========================================================

    return templates.TemplateResponse(
        request=request,
        name="set_password.html",
        context={
            "request": request,

            "engineer":
                engineer,

            "token":
                token,
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

    db: Session = Depends(
        get_db
    ),
):

    token = token.strip()


    # ========================================================
    # FIND ENGINEER
    # ========================================================

    engineer = (
        db.query(Engineer)
        .filter(
            Engineer.verification_token
            == token,

            Engineer.active
            == True,
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


    # ========================================================
    # PASSWORD ALREADY SET
    # ========================================================

    if engineer.password_hash:

        return templates.TemplateResponse(
            request=request,
            name="set_password.html",
            context={
                "request": request,

                "error":
                    "Password has already been configured.",
            },

            status_code=400,
        )


    # ========================================================
    # PASSWORD LENGTH
    # ========================================================

    if len(new_password) < 8:

        return templates.TemplateResponse(
            request=request,
            name="set_password.html",
            context={
                "request": request,

                "engineer":
                    engineer,

                "token":
                    token,

                "error": (
                    "Password must be at least "
                    "8 characters."
                ),
            },

            status_code=400,
        )


    # ========================================================
    # PASSWORD MATCH
    # ========================================================

    if new_password != confirm_password:

        return templates.TemplateResponse(
            request=request,
            name="set_password.html",
            context={
                "request": request,

                "engineer":
                    engineer,

                "token":
                    token,

                "error":
                    "Passwords do not match.",
            },

            status_code=400,
        )


    # ========================================================
    # SAVE PASSWORD
    # ========================================================

    engineer.password_hash = (
        hash_password(new_password)
    )

    engineer.password_set_at = (
        datetime.utcnow()
    )

    engineer.must_set_password = False


    # ========================================================
    # CONSUME INITIAL TOKEN
    # ========================================================

    engineer.verification_token = None

    engineer.last_login_at = (
        datetime.utcnow()
    )


    db.commit()


    # ========================================================
    # AUTOMATIC LOGIN
    # ========================================================

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
#
# Authenticated users can change their password whenever
# they want.
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

            "engineer":
                current,
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

    db: Session = Depends(
        get_db
    ),
):

    # ========================================================
    # CURRENT PASSWORD
    # ========================================================

    if not verify_password(
        current_password,
        current.password_hash,
    ):

        return templates.TemplateResponse(
            request=request,
            name="change_password.html",
            context={
                "request": request,

                "engineer":
                    current,

                "error":
                    "Current password is incorrect.",
            },

            status_code=400,
        )


    # ========================================================
    # NEW PASSWORD LENGTH
    # ========================================================

    if len(new_password) < 8:

        return templates.TemplateResponse(
            request=request,
            name="change_password.html",
            context={
                "request": request,

                "engineer":
                    current,

                "error": (
                    "New password must be at least "
                    "8 characters."
                ),
            },

            status_code=400,
        )


    # ========================================================
    # PASSWORD MATCH
    # ========================================================

    if new_password != confirm_password:

        return templates.TemplateResponse(
            request=request,
            name="change_password.html",
            context={
                "request": request,

                "engineer":
                    current,

                "error":
                    "New passwords do not match.",
            },

            status_code=400,
        )


    # ========================================================
    # SAVE NEW PASSWORD
    # ========================================================

    current.password_hash = (
        hash_password(new_password)
    )

    current.password_set_at = (
        datetime.utcnow()
    )

    current.must_set_password = False


    # ========================================================
    # INVALIDATE EXISTING RESET REQUEST
    # ========================================================

    current.password_reset_token = None

    current.password_reset_expires_at = None


    db.commit()


    # ========================================================
    # CREATE FRESH SESSION
    # ========================================================

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
# FORGOT PASSWORD PAGE
# ============================================================

@router.get(
    "/forgot-password",
    response_class=HTMLResponse,
)
def forgot_password_page(
    request: Request,
):

    return templates.TemplateResponse(
        request=request,
        name="forgot_password.html",
        context={
            "request": request,
        },
    )


# ============================================================
# FORGOT PASSWORD
#
# LAB FLOW:
#
# 1. User enters alias.
# 2. Internal reset token is generated.
# 3. Token is NOT displayed.
# 4. Same page displays the new-password form.
#
# No reset_password.html is required.
# ============================================================

@router.post(
    "/forgot-password",
    response_class=HTMLResponse,
)
def forgot_password(
    request: Request,

    username: str = Form(...),

    db: Session = Depends(
        get_db
    ),
):

    alias = username.strip().lower()


    # ========================================================
    # FIND ENGINEER
    # ========================================================

    engineer = (
        db.query(Engineer)
        .filter(
            Engineer.alias == alias,

            Engineer.active
            == True,
        )
        .first()
    )


    # ========================================================
    # UNKNOWN ACCOUNT
    #
    # Don't reveal whether an account exists.
    # ========================================================

    if engineer is None:

        return templates.TemplateResponse(
            request=request,
            name="forgot_password.html",
            context={
                "request": request,

                "message": (
                    "If the account exists, "
                    "a password reset option "
                    "will be available."
                ),
            },
        )


    # ========================================================
    # GENERATE INTERNAL RESET TOKEN
    # ========================================================

    token = (
        create_password_reset_token()
    )

    engineer.password_reset_token = token

    engineer.password_reset_expires_at = (
        password_reset_expiry()
    )


    db.commit()


    # ========================================================
    # SHOW PASSWORD FORM DIRECTLY
    #
    # IMPORTANT:
    #
    # The token is passed internally to the template.
    # It is NOT displayed to the user.
    # ========================================================

    return templates.TemplateResponse(
        request=request,
        name="forgot_password.html",
        context={
            "request": request,

            "engineer":
                engineer,

            "username":
                engineer.alias,

            "reset_ready":
                True,

            "reset_token":
                token,

            "expires_minutes":
                15,
        },
    )


# ============================================================
# RESET PASSWORD
#
# IMPORTANT:
#
# There is NO GET /reset-password page anymore.
#
# The user sets the password directly on the
# forgot_password.html page.
# ============================================================

@router.post(
    "/reset-password",
    response_class=HTMLResponse,
)
def reset_password(
    request: Request,

    token: str = Form(...),

    new_password: str = Form(...),

    confirm_password: str = Form(...),

    db: Session = Depends(
        get_db
    ),
):

    token = token.strip()


    # ========================================================
    # FIND ENGINEER USING RESET TOKEN
    # ========================================================

    engineer = (
        db.query(Engineer)
        .filter(
            Engineer.password_reset_token
            == token,

            Engineer.active
            == True,
        )
        .first()
    )


    # ========================================================
    # INVALID TOKEN
    # ========================================================

    if engineer is None:

        return templates.TemplateResponse(
            request=request,
            name="forgot_password.html",
            context={
                "request": request,

                "error": (
                    "This password reset request "
                    "is invalid or has already been used."
                ),
            },

            status_code=400,
        )


    # ========================================================
    # CHECK TOKEN EXPIRY
    # ========================================================

    if (
        not engineer.password_reset_expires_at
        or
        engineer.password_reset_expires_at
        < datetime.utcnow()
    ):

        return templates.TemplateResponse(
            request=request,
            name="forgot_password.html",
            context={
                "request": request,

                "error": (
                    "This password reset request "
                    "has expired. Please start again."
                ),
            },

            status_code=400,
        )


    # ========================================================
    # PASSWORD LENGTH
    # ========================================================

    if len(new_password) < 8:

        return templates.TemplateResponse(
            request=request,
            name="forgot_password.html",
            context={
                "request": request,

                "engineer":
                    engineer,

                "username":
                    engineer.alias,

                "reset_ready":
                    True,

                "reset_token":
                    token,

                "expires_minutes":
                    15,

                "error": (
                    "Password must be at least "
                    "8 characters."
                ),
            },

            status_code=400,
        )


    # ========================================================
    # PASSWORD MATCH
    # ========================================================

    if new_password != confirm_password:

        return templates.TemplateResponse(
            request=request,
            name="forgot_password.html",
            context={
                "request": request,

                "engineer":
                    engineer,

                "username":
                    engineer.alias,

                "reset_ready":
                    True,

                "reset_token":
                    token,

                "expires_minutes":
                    15,

                "error":
                    "Passwords do not match.",
            },

            status_code=400,
        )


    # ========================================================
    # SAVE NEW PASSWORD
    # ========================================================

    engineer.password_hash = (
        hash_password(new_password)
    )

    engineer.password_set_at = (
        datetime.utcnow()
    )

    engineer.must_set_password = False


    # ========================================================
    # CONSUME RESET TOKEN
    #
    # This makes the reset request one-time use.
    # ========================================================

    engineer.password_reset_token = None

    engineer.password_reset_expires_at = None


    engineer.last_login_at = (
        datetime.utcnow()
    )


    db.commit()


    # ========================================================
    # RETURN TO LOGIN
    # ========================================================

    return RedirectResponse(
        url="/login?reset=success",
        status_code=303,
    )


# ============================================================
# SESSION REFRESH
#
# Browser calls this every 5 minutes.
#
# refresh_session() extends the session by another hour.
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
        "status":
            "ok",

        "message":
            "Session refreshed",
    }


# ============================================================
# LOGOUT
# ============================================================

@router.post(
    "/logout"
)
def logout():

    response = RedirectResponse(
        url="/login",
        status_code=303,
    )

    clear_session(
        response
    )

    return response