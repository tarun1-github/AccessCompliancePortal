from datetime import datetime

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth import (
    clear_session,
    create_session,
    get_current_engineer,
    hash_password,
    verify_password,
)
from app.database import get_db
from app.models.engineer import Engineer

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"request": request},
    )


@router.post("/login", response_class=HTMLResponse)
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
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

    if engineer is None or not verify_password(
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
            },
            status_code=401,
        )

    engineer.last_login_at = datetime.utcnow()
    db.commit()

    if engineer.must_set_password or not engineer.password_hash:
        response = RedirectResponse(
            url="/set-password",
            status_code=303,
        )
        create_session(response, engineer)
        return response

    if str(engineer.role or "").upper() == "SUPERVISOR":
        destination = f"/{engineer.alias}"
    else:
        destination = f"/{engineer.alias}"

    response = RedirectResponse(
        url=destination,
        status_code=303,
    )
    create_session(response, engineer)
    return response


@router.get("/set-password", response_class=HTMLResponse)
def set_password_page(
    request: Request,
    current: Engineer = Depends(get_current_engineer),
):
    return templates.TemplateResponse(
        request=request,
        name="set_password.html",
        context={
            "request": request,
            "engineer": current,
        },
    )


@router.post("/set-password", response_class=HTMLResponse)
def set_password(
    request: Request,
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    current: Engineer = Depends(get_current_engineer),
    db: Session = Depends(get_db),
):
    if len(new_password) < 8:
        return templates.TemplateResponse(
            request=request,
            name="set_password.html",
            context={
                "request": request,
                "engineer": current,
                "error": "Password must be at least 8 characters.",
            },
            status_code=400,
        )

    if new_password != confirm_password:
        return templates.TemplateResponse(
            request=request,
            name="set_password.html",
            context={
                "request": request,
                "engineer": current,
                "error": "Passwords do not match.",
            },
            status_code=400,
        )

    current.password_hash = hash_password(new_password)
    current.password_set_at = datetime.utcnow()
    current.must_set_password = False
    db.commit()

    return RedirectResponse(
        url=f"/{current.alias}",
        status_code=303,
    )


@router.post("/change-password", response_class=HTMLResponse)
def change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    current: Engineer = Depends(get_current_engineer),
    db: Session = Depends(get_db),
):
    if not verify_password(current_password, current.password_hash):
        return templates.TemplateResponse(
            request=request,
            name="change_password.html",
            context={
                "request": request,
                "engineer": current,
                "error": "Current password is incorrect.",
            },
            status_code=400,
        )

    if len(new_password) < 8:
        return templates.TemplateResponse(
            request=request,
            name="change_password.html",
            context={
                "request": request,
                "engineer": current,
                "error": "New password must be at least 8 characters.",
            },
            status_code=400,
        )

    if new_password != confirm_password:
        return templates.TemplateResponse(
            request=request,
            name="change_password.html",
            context={
                "request": request,
                "engineer": current,
                "error": "New passwords do not match.",
            },
            status_code=400,
        )

    current.password_hash = hash_password(new_password)
    current.password_set_at = datetime.utcnow()
    current.must_set_password = False
    db.commit()

    return RedirectResponse(
        url=f"/{current.alias}",
        status_code=303,
    )


@router.get("/change-password", response_class=HTMLResponse)
def change_password_page(
    request: Request,
    current: Engineer = Depends(get_current_engineer),
):
    return templates.TemplateResponse(
        request=request,
        name="change_password.html",
        context={
            "request": request,
            "engineer": current,
        },
    )


@router.post("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=303)
    clear_session(response)
    return response
