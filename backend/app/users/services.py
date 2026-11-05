"""User profile and administrative role services."""

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.users.models import Role, User
from app.users.schemas import (
    RoleName,
    UserAdminUpdate,
    UserCreate,
    UserProfileUpdate,
)


def create_user(db: Session, payload: UserCreate) -> User:
    if payload.rol == RoleName.ADMINISTRADOR:
        raise HTTPException(
            status_code=403, detail="No se permite el autorregistro administrativo"
        )
    normalized_email = str(payload.email).lower()
    if db.scalar(select(User.id).where(User.email == normalized_email)):
        raise HTTPException(status_code=400, detail="El correo ya está registrado")
    if db.scalar(
        select(User.id).where(User.documento_identidad == payload.documento_identidad)
    ):
        raise HTTPException(status_code=400, detail="El documento ya está registrado")
    role = db.scalar(select(Role).where(Role.nombre_rol == payload.rol.value))
    if role is None:
        raise HTTPException(
            status_code=503, detail="El catálogo de roles no está inicializado"
        )
    user = User(
        email=normalized_email,
        password_hash=hash_password(payload.password),
        nombre_completo=payload.nombre_completo,
        documento_identidad=payload.documento_identidad,
        telefono=payload.telefono,
        roles=[role],
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user(db: Session, user_id: UUID) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


def list_users(db: Session, offset: int = 0, limit: int = 100) -> list[User]:
    return list(
        db.scalars(
            select(User)
            .order_by(User.fecha_creacion.desc())
            .offset(offset)
            .limit(limit)
        )
    )


def update_profile(db: Session, user: User, payload: UserProfileUpdate) -> User:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


def admin_update_user(db: Session, user: User, payload: UserAdminUpdate) -> User:
    data = payload.model_dump(exclude_unset=True)
    role_names = data.pop("roles", None)
    for field, value in data.items():
        setattr(user, field, value)
    if role_names is not None:
        roles = list(
            db.scalars(
                select(Role).where(Role.nombre_rol.in_([r.value for r in role_names]))
            )
        )
        if len(roles) != len(role_names):
            raise HTTPException(status_code=400, detail="Uno o más roles no existen")
        user.roles = roles
    db.commit()
    db.refresh(user)
    return user


def update_user_by_id(db: Session, user_id: UUID, payload: UserAdminUpdate) -> User:
    return admin_update_user(db, get_user(db, user_id), payload)


def create_role(db: Session, name: RoleName, description: str) -> Role:
    role = Role(nombre_rol=name.value, descripcion=description)
    db.add(role)
    db.commit()
    db.refresh(role)
    return role
