"""Auction closeout and ownership-scoped adjudication services."""

import secrets
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adjudications.models import Adjudication
from app.adjudications.schemas import PaymentStatus
from app.auctions.models import Auction
from app.bids.models import Bid
from app.cattle_lots.models import CattleLot
from app.users.models import User


def close_auction(db: Session, auction_id: UUID) -> Adjudication | None:
    auction = db.scalar(
        select(Auction).where(Auction.id == auction_id).with_for_update()
    )
    if auction is None:
        raise HTTPException(status_code=404, detail="Subasta no encontrada")
    if auction.estado_subasta in {"FINALIZADA", "DESIERTA"}:
        raise HTTPException(status_code=400, detail="La subasta ya fue cerrada")
    now = datetime.now(UTC)
    close_at = auction.fecha_cierre
    if close_at.tzinfo is None:
        close_at = close_at.replace(tzinfo=UTC)
    if now < close_at:
        raise HTTPException(
            status_code=400, detail="La subasta aún no alcanza su fecha de cierre"
        )

    winning_bid = db.scalar(
        select(Bid)
        .where(Bid.subasta_id == auction.id)
        .order_by(Bid.monto_ofertado_kilo.desc(), Bid.fecha_hora_puja.asc())
        .limit(1)
    )
    lot = db.get(CattleLot, auction.lote_id)
    if winning_bid is None:
        auction.estado_subasta = "DESIERTA"
        lot.estado_lote = "DISPONIBLE"
        db.commit()
        return None

    total = (
        winning_bid.monto_ofertado_kilo
        * Decimal(lot.cantidad_cabezas)
        * Decimal(str(lot.peso_promedio_kg))
    ).quantize(Decimal("0.01"))
    act = Adjudication(
        subasta_id=auction.id,
        comprador_ganador_id=winning_bid.comprador_id,
        puja_ganadora_id=winning_bid.id,
        monto_total_final=total,
        guia_movilizacion_codigo=f"SAG-{secrets.token_urlsafe(18)}",
        estado_pago="PENDIENTE",
        fecha_cierre=now,
    )
    auction.estado_subasta = "FINALIZADA"
    lot.estado_lote = "ADJUDICADO"
    db.add(act)
    db.commit()
    db.refresh(act)
    return act


def list_adjudications(
    db: Session, *, buyer_id: UUID | None = None, offset: int = 0, limit: int = 100
) -> list[Adjudication]:
    query = (
        select(Adjudication)
        .order_by(Adjudication.fecha_cierre.desc())
        .offset(offset)
        .limit(limit)
    )
    if buyer_id is not None:
        query = query.where(Adjudication.comprador_ganador_id == buyer_id)
    return list(db.scalars(query))


def update_payment_status(
    db: Session, adjudication: Adjudication, status: PaymentStatus
) -> Adjudication:
    adjudication.estado_pago = status.value
    db.commit()
    db.refresh(adjudication)
    return adjudication


def update_payment_status_by_id(
    db: Session, adjudication_id: UUID, status: PaymentStatus
) -> Adjudication:
    adjudication = db.get(Adjudication, adjudication_id)
    if adjudication is None:
        raise HTTPException(status_code=404, detail="Acta no encontrada")
    return update_payment_status(db, adjudication, status)


def list_adjudications_for_user(
    db: Session, user: User, *, offset: int = 0, limit: int = 100
) -> list[Adjudication]:
    roles = {role.nombre_rol for role in user.roles}
    if "ADMINISTRADOR" in roles:
        return list_adjudications(db, offset=offset, limit=limit)
    if "COMPRADOR" in roles:
        return list_adjudications(db, buyer_id=user.id, offset=offset, limit=limit)
    raise HTTPException(status_code=403, detail="Acceso reservado a compradores")


def get_adjudication_for_user(
    db: Session, adjudication_id: UUID, user: User
) -> Adjudication:
    adjudication = db.get(Adjudication, adjudication_id)
    if adjudication is None:
        raise HTTPException(status_code=404, detail="Acta no encontrada")
    roles = {role.nombre_rol for role in user.roles}
    if "ADMINISTRADOR" not in roles and adjudication.comprador_ganador_id != user.id:
        raise HTTPException(status_code=404, detail="Acta no encontrada")
    return adjudication
