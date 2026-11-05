"""Auction scheduling, visibility, and lifecycle services."""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auctions.models import Auction
from app.auctions.schemas import AuctionCreate, AuctionUpdate
from app.bids.models import Bid
from app.cattle_lots.models import CattleLot
from app.users.models import User


def schedule_auction(
    db: Session, payload: AuctionCreate, actor: User, *, is_admin: bool
) -> Auction:
    lot = db.get(CattleLot, payload.lote_id)
    if lot is None:
        raise HTTPException(status_code=404, detail="Lote no encontrado")
    if not is_admin and lot.ganadero_id != actor.id:
        raise HTTPException(status_code=404, detail="Lote no encontrado")
    if lot.estado_lote != "DISPONIBLE":
        raise HTTPException(status_code=400, detail="El lote no está disponible")
    if db.scalar(select(Auction.id).where(Auction.lote_id == lot.id)):
        raise HTTPException(
            status_code=400, detail="El lote ya tiene una subasta registrada"
        )
    if payload.fecha_inicio <= datetime.now(UTC):
        raise HTTPException(
            status_code=400, detail="La fecha de inicio debe estar en el futuro"
        )
    auction = Auction(**payload.model_dump(), estado_subasta="PROGRAMADA")
    lot.estado_lote = "EN_SUBASTA"
    db.add(auction)
    db.commit()
    db.refresh(auction)
    return auction


def list_auctions(
    db: Session,
    *,
    status_filter: str | None = None,
    owner_id: UUID | None = None,
    active_only: bool = False,
    offset: int = 0,
    limit: int = 100,
) -> list[Auction]:
    now = datetime.now(UTC)
    query = (
        select(Auction)
        .join(CattleLot)
        .order_by(Auction.fecha_inicio)
        .offset(offset)
        .limit(limit)
    )
    if owner_id is not None:
        query = query.where(CattleLot.ganadero_id == owner_id)
    if active_only:
        query = query.where(Auction.fecha_inicio <= now, Auction.fecha_cierre > now)
    elif status_filter:
        query = query.where(Auction.estado_subasta == status_filter)
    auctions = list(db.scalars(query).unique())
    for auction in auctions:
        if auction.estado_subasta in {"FINALIZADA", "DESIERTA"}:
            continue
        if now < auction.fecha_inicio:
            auction.estado_subasta = "PROGRAMADA"
        elif now < auction.fecha_cierre:
            auction.estado_subasta = "ACTIVA"
    return auctions


def get_auction(db: Session, auction_id: UUID) -> Auction:
    auction = db.get(Auction, auction_id)
    if auction is None:
        raise HTTPException(status_code=404, detail="Subasta no encontrada")
    return auction


def get_active_auction(db: Session, auction_id: UUID) -> Auction:
    now = datetime.now(UTC)
    auction = db.scalar(
        select(Auction).where(
            Auction.id == auction_id,
            Auction.fecha_inicio <= now,
            Auction.fecha_cierre > now,
        )
    )
    if auction is None:
        raise HTTPException(status_code=404, detail="Subasta no encontrada")
    return auction


def update_auction(db: Session, auction_id: UUID, payload: AuctionUpdate) -> Auction:
    auction = db.scalar(
        select(Auction).where(Auction.id == auction_id).with_for_update()
    )
    if auction is None:
        raise HTTPException(status_code=404, detail="Subasta no encontrada")
    start = auction.fecha_inicio
    if start.tzinfo is None:
        start = start.replace(tzinfo=UTC)
    if auction.estado_subasta != "PROGRAMADA" or datetime.now(UTC) >= start:
        raise HTTPException(
            status_code=400, detail="Solo se puede editar una subasta aún no iniciada"
        )
    if db.scalar(select(Bid.id).where(Bid.subasta_id == auction.id)):
        raise HTTPException(
            status_code=400, detail="No se puede editar una subasta con pujas"
        )

    data = payload.model_dump(exclude_unset=True)
    new_start = data.get("fecha_inicio", auction.fecha_inicio)
    new_close = data.get("fecha_cierre", auction.fecha_cierre)
    if new_start.tzinfo is None:
        new_start = new_start.replace(tzinfo=UTC)
    if new_close.tzinfo is None:
        new_close = new_close.replace(tzinfo=UTC)
    if new_close <= new_start or new_start <= datetime.now(UTC):
        raise HTTPException(
            status_code=400, detail="El rango de fechas de la subasta no es válido"
        )
    for field, value in data.items():
        setattr(auction, field, value)
    db.commit()
    db.refresh(auction)
    return auction


def list_auctions_for_user(
    db: Session, user: User, *, offset: int = 0, limit: int = 100
) -> list[Auction]:
    roles = {role.nombre_rol for role in user.roles}
    if "ADMINISTRADOR" in roles:
        return list_auctions(db, offset=offset, limit=limit)
    if "GANADERO" in roles:
        return list_auctions(db, owner_id=user.id, offset=offset, limit=limit)
    if "COMPRADOR" in roles:
        return list_auctions(db, active_only=True, offset=offset, limit=limit)
    raise HTTPException(status_code=403, detail="Rol no autorizado")


def schedule_auction_for_user(
    db: Session, payload: AuctionCreate, actor: User
) -> Auction:
    roles = {role.nombre_rol for role in actor.roles}
    if not roles.intersection({"ADMINISTRADOR", "GANADERO"}):
        raise HTTPException(
            status_code=403,
            detail="Solo un ganadero puede programar una subasta",
        )
    return schedule_auction(db, payload, actor, is_admin="ADMINISTRADOR" in roles)


def get_auction_for_user(db: Session, auction_id: UUID, user: User) -> Auction:
    roles = {role.nombre_rol for role in user.roles}
    if "ADMINISTRADOR" in roles:
        return get_auction(db, auction_id)
    if "GANADERO" in roles:
        auction = get_auction(db, auction_id)
        if auction.lote.ganadero_id != user.id:
            raise HTTPException(status_code=404, detail="Subasta no encontrada")
        return auction
    if "COMPRADOR" in roles:
        return get_active_auction(db, auction_id)
    raise HTTPException(status_code=403, detail="Rol no autorizado")


def update_auction_for_user(
    db: Session, auction_id: UUID, user: User, payload: AuctionUpdate
) -> Auction:
    roles = {role.nombre_rol for role in user.roles}
    if not roles.intersection({"ADMINISTRADOR", "GANADERO"}):
        raise HTTPException(
            status_code=403, detail="No tienes permisos para editar subastas"
        )
    auction = get_auction(db, auction_id)
    if "ADMINISTRADOR" not in roles and auction.lote.ganadero_id != user.id:
        raise HTTPException(status_code=404, detail="Subasta no encontrada")
    return update_auction(db, auction_id, payload)
