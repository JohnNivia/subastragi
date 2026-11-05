"""Bid placement and history access services."""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auctions.models import Auction
from app.bids.models import Bid
from app.bids.schemas import BidCreate
from app.users.models import User


def place_bid(db: Session, payload: BidCreate, buyer: User) -> Bid:
    if "COMPRADOR" not in {role.nombre_rol for role in buyer.roles}:
        raise HTTPException(
            status_code=403, detail="Solo los compradores pueden realizar pujas"
        )
    auction = db.scalar(
        select(Auction).where(Auction.id == payload.subasta_id).with_for_update()
    )
    if auction is None:
        raise HTTPException(status_code=404, detail="Subasta no encontrada")
    now = datetime.now(UTC)
    if auction.fecha_inicio.tzinfo is None:
        auction_start = auction.fecha_inicio.replace(tzinfo=UTC)
    else:
        auction_start = auction.fecha_inicio
    if auction.fecha_cierre.tzinfo is None:
        auction_close = auction.fecha_cierre.replace(tzinfo=UTC)
    else:
        auction_close = auction.fecha_cierre
    if now < auction_start or now >= auction_close:
        raise HTTPException(status_code=400, detail="La subasta no está abierta")
    if auction.lote.ganadero_id == buyer.id:
        raise HTTPException(
            status_code=403, detail="No puedes pujar por tu propio lote"
        )
    if auction.estado_subasta in {"FINALIZADA", "DESIERTA"}:
        raise HTTPException(status_code=400, detail="La subasta ya está cerrada")

    highest = db.scalar(
        select(Bid.monto_ofertado_kilo)
        .where(Bid.subasta_id == auction.id)
        .order_by(Bid.monto_ofertado_kilo.desc(), Bid.fecha_hora_puja.asc())
        .limit(1)
    )
    minimum = (
        auction.precio_base_kilo
        if highest is None
        else highest + auction.incremento_minimo_puja
    )
    if payload.monto_ofertado_kilo < minimum:
        raise HTTPException(
            status_code=400,
            detail=f"La oferta mínima permitida es {minimum}",
        )
    bid = Bid(
        subasta_id=auction.id,
        comprador_id=buyer.id,
        monto_ofertado_kilo=payload.monto_ofertado_kilo,
        fecha_hora_puja=now,
    )
    auction.estado_subasta = "ACTIVA"
    db.add(bid)
    db.commit()
    db.refresh(bid)
    return bid


def list_bids(
    db: Session, *, buyer_id: UUID | None = None, offset: int = 0, limit: int = 100
) -> list[Bid]:
    query = select(Bid).order_by(Bid.fecha_hora_puja.desc()).offset(offset).limit(limit)
    if buyer_id is not None:
        query = query.where(Bid.comprador_id == buyer_id)
    return list(db.scalars(query))


def list_bids_for_user(
    db: Session, user: User, *, offset: int = 0, limit: int = 100
) -> list[Bid]:
    roles = {role.nombre_rol for role in user.roles}
    if "ADMINISTRADOR" in roles:
        return list_bids(db, offset=offset, limit=limit)
    if "COMPRADOR" in roles:
        return list_bids(db, buyer_id=user.id, offset=offset, limit=limit)
    raise HTTPException(status_code=403, detail="Acceso reservado a compradores")


def get_bid_for_user(db: Session, bid_id: UUID, user: User) -> Bid:
    bid = db.get(Bid, bid_id)
    if bid is None:
        raise HTTPException(status_code=404, detail="Puja no encontrada")
    roles = {role.nombre_rol for role in user.roles}
    if "ADMINISTRADOR" not in roles and bid.comprador_id != user.id:
        raise HTTPException(status_code=404, detail="Puja no encontrada")
    return bid
