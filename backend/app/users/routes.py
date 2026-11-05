"""Self-service profile and administrator-only user management endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.users import services
from app.users.models import User
from app.users.schemas import UserAdminUpdate, UserProfileUpdate, UserRead

router = APIRouter(prefix="/users", tags=["Usuarios"])


@router.get("/me", response_model=UserRead)
def read_me(user: User = Depends(get_current_user)) -> UserRead:
    return user


@router.patch("/me", response_model=UserRead)
def update_me(
    payload: UserProfileUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> UserRead:
    return services.update_profile(db, user, payload)


@router.get("", response_model=list[UserRead])
def list_users(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles("ADMINISTRADOR")),
) -> list[UserRead]:
    return services.list_users(db, offset, limit)


@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    user_id: UUID,
    payload: UserAdminUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles("ADMINISTRADOR")),
) -> UserRead:
    return services.update_user_by_id(db, user_id, payload)
