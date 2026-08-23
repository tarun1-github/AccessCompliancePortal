import base64
import hashlib
import hmac
import json
import os
import secrets
import time

from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.engineer import Engineer


# ============================================================
# SESSION CONFIGURATION
# ============================================================

SESSION_COOKIE = "ac_session"

# User should remain logged in for 1 hour.
SESSION_MAX_AGE = 60 * 60


# ============================================================
# PASSWORD CONFIGURATION
# ============================================================

PBKDF2_ITERATIONS = 310_000


# ============================================================
# PASSWORD RESET CONFIGURATION
# ============================================================

# Forgot-password reset links remain valid for 15 minutes.
PASSWORD_RESET_MINUTES = 15


# ============================================================
# AUTH SECRET
# ============================================================

def _secret() -> bytes:

    value = os.getenv(
        "AUTH_SECRET_KEY"
    )

    if not value:

        raise RuntimeError(
            "AUTH_SECRET_KEY is not configured. "
            "Add a long random secret to .env."
        )

    return value.encode("utf-8")


# ============================================================
# PASSWORD HASH
# ============================================================

def hash_password(
    password: str,
) -> str:

    if len(password) < 8:

        raise ValueError(
            "Password must be at least 8 characters."
        )

    salt = secrets.token_bytes(16)

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )

    return (
        f"pbkdf2_sha256${PBKDF2_ITERATIONS}$"
        f"{base64.urlsafe_b64encode(salt).decode()}$"
        f"{base64.urlsafe_b64encode(digest).decode()}"
    )


# ============================================================
# PASSWORD VERIFY
# ============================================================

def verify_password(
    password: str,
    encoded: Optional[str],
) -> bool:

    if not encoded:

        return False

    try:

        scheme, iterations, salt_b64, digest_b64 = (
            encoded.split("$", 3)
        )

        if scheme != "pbkdf2_sha256":

            return False

        salt = base64.urlsafe_b64decode(
            salt_b64.encode()
        )

        expected = base64.urlsafe_b64decode(
            digest_b64.encode()
        )

        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            int(iterations),
        )

        return hmac.compare_digest(
            actual,
            expected,
        )

    except Exception:

        return False


# ============================================================
# SESSION SIGNING
# ============================================================

def _sign(
    payload: str,
) -> str:

    signature = hmac.new(
        _secret(),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return (
        f"{payload}.{signature}"
    )


# ============================================================
# SESSION VERIFY
# ============================================================

def _verify(
    value: str,
) -> Optional[dict]:

    try:

        payload, signature = value.rsplit(
            ".",
            1,
        )

        expected = hmac.new(
            _secret(),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(
            signature,
            expected,
        ):

            return None

        raw = (
            base64.urlsafe_b64decode(
                payload.encode()
            )
            .decode()
        )

        data = json.loads(raw)

        if data.get(
            "exp",
            0,
        ) < time.time():

            return None

        return data

    except Exception:

        return None


# ============================================================
# CREATE SESSION
# ============================================================

def create_session(
    response,
    engineer: Engineer,
):

    data = {

        "engineer_id":
            engineer.id,

        "role":
            str(
                engineer.role
                or "ENGINEER"
            ).upper(),

        "exp":
            int(
                time.time()
            )
            + SESSION_MAX_AGE,

        "nonce":
            secrets.token_hex(8),
    }

    payload = (
        base64.urlsafe_b64encode(
            json.dumps(
                data,
                separators=(
                    ",",
                    ":",
                ),
            ).encode()
        )
        .decode()
    )

    response.set_cookie(

        SESSION_COOKIE,

        _sign(payload),

        max_age=SESSION_MAX_AGE,

        httponly=True,

        # Current LAB is HTTP.
        # Change to True when deployed on HTTPS.
        secure=False,

        samesite="lax",

        path="/",
    )


# ============================================================
# REFRESH SESSION
#
# Called by browser every 5 minutes.
#
# This gives an active user another 1 hour.
# ============================================================

def refresh_session(
    response,
    engineer: Engineer,
):

    create_session(
        response,
        engineer,
    )


# ============================================================
# CLEAR SESSION
# ============================================================

def clear_session(
    response,
):

    response.delete_cookie(
        SESSION_COOKIE,
        path="/",
    )


# ============================================================
# GET CURRENT ENGINEER
# ============================================================

def get_current_engineer(
    request: Request,

    db: Session = Depends(
        get_db
    ),
) -> Engineer:

    raw = request.cookies.get(
        SESSION_COOKIE
    )

    if not raw:

        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    session = _verify(
        raw
    )

    if not session:

        raise HTTPException(
            status_code=401,
            detail="Session expired or invalid",
        )

    try:

        engineer_id = int(
            session[
                "engineer_id"
            ]
        )

    except (
        KeyError,
        ValueError,
        TypeError,
    ):

        raise HTTPException(
            status_code=401,
            detail="Invalid authentication session",
        )

    engineer = (
        db.query(Engineer)
        .filter(
            Engineer.id
            == engineer_id,

            Engineer.active
            == True,
        )
        .first()
    )

    if engineer is None:

        raise HTTPException(
            status_code=401,
            detail="User is inactive or not found",
        )

    return engineer


# ============================================================
# REQUIRE SUPERVISOR
# ============================================================

def require_supervisor(
    current: Engineer = Depends(
        get_current_engineer
    ),
) -> Engineer:

    if (
        str(
            current.role
            or ""
        ).upper()
        != "SUPERVISOR"
    ):

        raise HTTPException(
            status_code=403,
            detail="Supervisor access required",
        )

    return current


# ============================================================
# REQUIRE OWN ENGINEER
# ============================================================

def require_own_engineer(
    engineer_id: int,

    current: Engineer = Depends(
        get_current_engineer
    ),
) -> Engineer:

    if int(
        current.id
    ) != int(
        engineer_id
    ):

        raise HTTPException(
            status_code=403,
            detail=(
                "You are not authorized "
                "to access another engineer's page."
            ),
        )

    return current


# ============================================================
# LOGIN REDIRECT
# ============================================================

def login_redirect(
    request: Request,
):

    return RedirectResponse(
        url="/login",
        status_code=303,
    )


# ============================================================
# PASSWORD RESET TOKEN
# ============================================================

def create_password_reset_token() -> str:

    """
    Generate a cryptographically secure
    password reset token.
    """

    return secrets.token_urlsafe(48)


# ============================================================
# PASSWORD RESET EXPIRY
# ============================================================

def password_reset_expiry() -> datetime:

    """
    Return password reset token expiry time.
    Default: 15 minutes.
    """

    return (
        datetime.utcnow()
        + timedelta(
            minutes=PASSWORD_RESET_MINUTES
        )
    )