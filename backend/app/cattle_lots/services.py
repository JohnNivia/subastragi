"""Breed catalog and ownership-scoped cattle lot services."""

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.cattle_lots.models import Breed, CattleLot
from app.cattle_lots.schemas import BreedUpdate, CattleLotCreate, CattleLotUpdate
from app.users.models import User


def create_breed(db: Session, nombre_raza: str, proposito: str) -> Breed:
    breed = Breed(nombre_raza=nombre_raza, proposito=proposito)
    db.add(breed)
    db.commit()
    db.refresh(breed)
    return breed


def list_breeds(db: Session, *, include_inactive: bool = False) -> list[Breed]:
    query = select(Breed).order_by(Breed.nombre_raza)
    if not include_inactive:
        query = query.where(Breed.estado.is_(True))
    return list(db.scalars(query))


def update_breed(db: Session, breed_id: UUID, payload: BreedUpdate) -> Breed:
    breed = db.get(Breed, breed_id)
    if breed is None:
        raise HTTPException(status_code=404, detail="Raza no encontrada")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(breed, field, value)
    db.commit()
    db.refresh(breed)
    return breed


def create_lot(db: Session, payload: CattleLotCreate, seller_id: UUID) -> CattleLot:
    breed = db.get(Breed, payload.raza_id)
    if breed is None or not breed.estado:
        raise HTTPException(status_code=400, detail="La raza no existe o está inactiva")
    if db.scalar(
        select(CattleLot.id).where(CattleLot.codigo_lote == payload.codigo_lote)
    ):
        raise HTTPException(
            status_code=400, detail="El código de lote ya está registrado"
        )
    lot = CattleLot(**payload.model_dump(), ganadero_id=seller_id)
    db.add(lot)
    db.commit()
    db.refresh(lot)
    return lot


def list_lots(
    db: Session, *, owner_id: UUID | None = None, offset: int = 0, limit: int = 100
) -> list[CattleLot]:
    query = (
        select(CattleLot).order_by(CattleLot.codigo_lote).offset(offset).limit(limit)
    )
    if owner_id is not None:
        query = query.where(CattleLot.ganadero_id == owner_id)
    return list(db.scalars(query))


def get_lot(db: Session, lot_id: UUID, *, owner_id: UUID | None = None) -> CattleLot:
    lot = db.get(CattleLot, lot_id)
    if lot is None or (owner_id is not None and lot.ganadero_id != owner_id):
        raise HTTPException(status_code=404, detail="Lote no encontrado")
    return lot


def update_lot(db: Session, lot: CattleLot, payload: CattleLotUpdate) -> CattleLot:
    data = payload.model_dump(exclude_unset=True)
    if "raza_id" in data:
        breed = db.get(Breed, data["raza_id"])
        if breed is None or not breed.estado:
            raise HTTPException(
                status_code=400, detail="La raza no existe o está inactiva"
            )
    if lot.estado_lote != "DISPONIBLE":
        raise HTTPException(
            status_code=400, detail="No se puede editar un lote que ya está subastado"
        )
    for field, value in data.items():
        setattr(lot, field, value)
    db.commit()
    db.refresh(lot)
    return lot


def set_lot_status(db: Session, lot: CattleLot, estado: str) -> CattleLot:
    if estado not in {"DISPONIBLE", "SUSPENDIDO"}:
        raise HTTPException(status_code=422, detail="Estado de lote no permitido")
    lot.estado_lote = estado
    db.commit()
    db.refresh(lot)
    return lot


def list_lots_for_user(
    db: Session, user: User, *, offset: int = 0, limit: int = 100
) -> list[CattleLot]:
    roles = {role.nombre_rol for role in user.roles}
    if "ADMINISTRADOR" in roles:
        return list_lots(db, offset=offset, limit=limit)
    if "GANADERO" in roles:
        return list_lots(db, owner_id=user.id, offset=offset, limit=limit)
    raise HTTPException(status_code=403, detail="Acceso reservado a ganaderos")


def get_lot_for_user(db: Session, lot_id: UUID, user: User) -> CattleLot:
    roles = {role.nombre_rol for role in user.roles}
    if "ADMINISTRADOR" in roles:
        return get_lot(db, lot_id)
    if "GANADERO" not in roles:
        raise HTTPException(status_code=403, detail="Acceso reservado a ganaderos")
    return get_lot(db, lot_id, owner_id=user.id)


def update_lot_for_user(
    db: Session, lot_id: UUID, user: User, payload: CattleLotUpdate
) -> CattleLot:
    lot = get_lot_for_user(db, lot_id, user)
    return update_lot(db, lot, payload)


def set_lot_status_by_id(db: Session, lot_id: UUID, estado: str) -> CattleLot:
    return set_lot_status(db, get_lot(db, lot_id), estado)
