"""Breed catalog and ownership-protected lot endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.cattle_lots import services
from app.cattle_lots.schemas import (
    BreedCreate,
    BreedRead,
    BreedUpdate,
    CattleLotCreate,
    CattleLotRead,
    CattleLotStatusUpdate,
    CattleLotUpdate,
)
from app.core.database import get_db
from app.core.dependencies import require_roles
from app.users.models import User

router = APIRouter(tags=["Ganado"])


@router.get("/breeds", response_model=list[BreedRead])
def list_breeds(db: Session = Depends(get_db)) -> list[BreedRead]:
    return services.list_breeds(db)


@router.post("/breeds", response_model=BreedRead, status_code=201)
def create_breed(
    payload: BreedCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles("ADMINISTRADOR")),
) -> BreedRead:
    return services.create_breed(db, **payload.model_dump())


@router.patch("/breeds/{breed_id}", response_model=BreedRead)
def update_breed(
    breed_id: UUID,
    payload: BreedUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles("ADMINISTRADOR")),
) -> BreedRead:
    return services.update_breed(db, breed_id, payload)


@router.get("/lots", response_model=list[CattleLotRead])
def list_lots(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("ADMINISTRADOR", "GANADERO")),
) -> list[CattleLotRead]:
    return services.list_lots_for_user(db, user, offset=offset, limit=limit)


@router.post("/lots", response_model=CattleLotRead, status_code=201)
def create_lot(
    payload: CattleLotCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("GANADERO")),
) -> CattleLotRead:
    return services.create_lot(db, payload, user.id)


@router.get("/lots/{lot_id}", response_model=CattleLotRead)
def get_lot(
    lot_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("ADMINISTRADOR", "GANADERO")),
) -> CattleLotRead:
    return services.get_lot_for_user(db, lot_id, user)


@router.patch("/lots/{lot_id}", response_model=CattleLotRead)
def update_lot(
    lot_id: UUID,
    payload: CattleLotUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("GANADERO", "ADMINISTRADOR")),
) -> CattleLotRead:
    return services.update_lot_for_user(db, lot_id, user, payload)


@router.patch("/lots/{lot_id}/status", response_model=CattleLotRead)
def update_lot_status(
    lot_id: UUID,
    payload: CattleLotStatusUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles("ADMINISTRADOR")),
) -> CattleLotRead:
    return services.set_lot_status_by_id(db, lot_id, payload.estado_lote)
