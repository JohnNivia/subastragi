"""Authentication endpoints, including secure refresh-cookie handling."""

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.auth import services
from app.auth.schemas import (
    LoginRequest,
    LogoutResponse,
    PasswordChangeRequest,
    RegisterRequest,
    TokenResponse,
)
from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.users.models import User
from app.users.schemas import UserRead

router = APIRouter(prefix="/auth", tags=["Autenticación"])
COOKIE_PATH = "/api/v1/auth"


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.cookie_name,
        value=token,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        httponly=True,
        secure=settings.environment == "production",
        samesite="lax",
        path=COOKIE_PATH,
    )


def _check_cookie_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    if origin and origin not in settings.cors_origins:
        raise HTTPException(status_code=403, detail="Origen no permitido")


@router.post("/register", response_model=UserRead, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> UserRead:
    return services.register(db, **payload.model_dump())


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest, response: Response, db: Session = Depends(get_db)
) -> TokenResponse:
    user, access_token, refresh_token = services.authenticate(
        db, payload.email, payload.password
    )
    _set_refresh_cookie(response, refresh_token)
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.access_token_expire_minutes * 60,
        usuario=user,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    request: Request, response: Response, db: Session = Depends(get_db)
) -> TokenResponse:
    _check_cookie_origin(request)
    token = request.cookies.get(settings.cookie_name)
    if not token:
        raise HTTPException(status_code=401, detail="Refresh token requerido")
    user, access_token, refresh_token = services.rotate_refresh_token(db, token)
    _set_refresh_cookie(response, refresh_token)
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.access_token_expire_minutes * 60,
        usuario=user,
    )


@router.post("/logout", response_model=LogoutResponse)
def logout(
    request: Request, response: Response, db: Session = Depends(get_db)
) -> LogoutResponse:
    _check_cookie_origin(request)
    services.revoke_refresh_token(db, request.cookies.get(settings.cookie_name))
    response.delete_cookie(
        key=settings.cookie_name,
        path=COOKIE_PATH,
        httponly=True,
        secure=settings.environment == "production",
        samesite="lax",
    )
    return LogoutResponse()


@router.post("/password", status_code=204)
def change_password(
    payload: PasswordChangeRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    services.change_password(db, user, payload.current_password, payload.new_password)
