"""Reusable authentication and role-based authorization dependencies."""

from collections.abc import Callable
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.users.models import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Resolve an active user from an access token."""
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas o expiradas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized
    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise unauthorized
    try:
        user_id = UUID(str(payload.get("sub")))
    except ValueError:
        raise unauthorized from None
    user = db.get(User, user_id)
    if user is None or not user.estado:
        raise unauthorized
    return user


def require_roles(*allowed_roles: str) -> Callable[..., User]:
    """Build a dependency that requires at least one named role."""

    def role_dependency(user: User = Depends(get_current_user)) -> User:
        user_roles = {role.nombre_rol for role in user.roles}
        if user_roles.isdisjoint(allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para realizar esta operación",
            )
        return user

    return role_dependency
