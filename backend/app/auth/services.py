"""Registration, login, and stateful refresh-token rotation services."""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.auth.models import RefreshSession
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.users import services as user_services
from app.users.models import User
from app.users.schemas import RoleName, UserCreate


def register(
    db: Session,
    *,
    email: str,
    password: str,
    nombre_completo: str,
    documento_identidad: str,
    telefono: str | None,
    rol: RoleName,
) -> User:
    return user_services.create_user(
        db,
        UserCreate(
            email=email,
            password=password,
            nombre_completo=nombre_completo,
            documento_identidad=documento_identidad,
            telefono=telefono,
            rol=rol,
        ),
    )


def authenticate(db: Session, email: str, password: str) -> tuple[User, str, str]:
    user = db.scalar(select(User).where(User.email == email.lower()))
    if (
        user is None
        or not verify_password(password, user.password_hash)
        or not user.estado
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    refresh_id = uuid4()
    refresh_expires = datetime.now(UTC) + timedelta(
        days=settings.refresh_token_expire_days
    )
    db.add(RefreshSession(id=refresh_id, usuario_id=user.id, vence_en=refresh_expires))
    db.commit()
    access = create_access_token(user.id, [role.nombre_rol for role in user.roles])
    refresh = create_refresh_token(user.id, refresh_id)
    return user, access, refresh


def rotate_refresh_token(db: Session, token: str) -> tuple[User, str, str]:
    payload = decode_token(token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Refresh token inválido o expirado")
    try:
        session_id = UUID(str(payload.get("jti")))
        user_id = UUID(str(payload.get("sub")))
    except ValueError:
        raise HTTPException(
            status_code=401, detail="Refresh token inválido o expirado"
        ) from None

    session = db.scalar(
        select(RefreshSession).where(RefreshSession.id == session_id).with_for_update()
    )
    now = datetime.now(UTC)
    expiry = session.vence_en if session else None
    if expiry is not None and expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=UTC)
    user = db.get(User, user_id)
    if (
        session is None
        or session.usuario_id != user_id
        or session.revocada_en is not None
        or expiry is None
        or expiry <= now
        or user is None
        or not user.estado
    ):
        raise HTTPException(status_code=401, detail="Refresh token inválido o revocado")

    session.revocada_en = now
    new_id = uuid4()
    new_expiry = now + timedelta(days=settings.refresh_token_expire_days)
    db.add(RefreshSession(id=new_id, usuario_id=user.id, vence_en=new_expiry))
    db.commit()
    access = create_access_token(user.id, [role.nombre_rol for role in user.roles])
    return user, access, create_refresh_token(user.id, new_id)


def revoke_refresh_token(db: Session, token: str | None) -> None:
    if not token:
        return
    payload = decode_token(token)
    if not payload or payload.get("type") != "refresh":
        return
    try:
        session_id = UUID(str(payload.get("jti")))
    except ValueError:
        return
    session = db.get(RefreshSession, session_id)
    if session is not None and session.revocada_en is None:
        session.revocada_en = datetime.now(UTC)
        db.commit()


def change_password(
    db: Session, user: User, current_password: str, new_password: str
) -> None:
    if not verify_password(current_password, user.password_hash):
        raise HTTPException(
            status_code=400, detail="La contraseña actual no es correcta"
        )
    if verify_password(new_password, user.password_hash):
        raise HTTPException(
            status_code=400, detail="La contraseña nueva debe ser diferente"
        )
    user.password_hash = hash_password(new_password)
    db.execute(
        update(RefreshSession)
        .where(
            RefreshSession.usuario_id == user.id, RefreshSession.revocada_en.is_(None)
        )
        .values(revocada_en=datetime.now(UTC))
    )
    db.commit()
