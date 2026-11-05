"""Auction finalization and buyer-owned adjudication endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.adjudications import services
from app.adjudications.schemas import AdjudicationPaymentUpdate, AdjudicationRead
from app.core.database import get_db
from app.core.dependencies import require_roles
from app.users.models import User

router = APIRouter(prefix="/adjudications", tags=["Adjudicaciones"])


@router.patch("/{adjudication_id}/payment", response_model=AdjudicationRead)
def update_payment_status(
    adjudication_id: UUID,
    payload: AdjudicationPaymentUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles("ADMINISTRADOR")),
) -> AdjudicationRead:
    return services.update_payment_status_by_id(
        db, adjudication_id, payload.estado_pago
    )


@router.post("/auctions/{auction_id}/close", response_model=AdjudicationRead | None)
def close_auction(
    auction_id: UUID,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles("ADMINISTRADOR")),
) -> AdjudicationRead | None:
    return services.close_auction(db, auction_id)


@router.get("", response_model=list[AdjudicationRead])
def list_adjudications(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("ADMINISTRADOR", "COMPRADOR")),
) -> list[AdjudicationRead]:
    return services.list_adjudications_for_user(db, user, offset=offset, limit=limit)


@router.get("/{adjudication_id}", response_model=AdjudicationRead)
def read_adjudication(
    adjudication_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("ADMINISTRADOR", "COMPRADOR")),
) -> AdjudicationRead:
    return services.get_adjudication_for_user(db, adjudication_id, user)
