"""Bid placement and buyer-owned bid history endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.bids import services
from app.bids.schemas import BidCreate, BidRead
from app.core.database import get_db
from app.core.dependencies import require_roles
from app.users.models import User

router = APIRouter(prefix="/bids", tags=["Pujas"])


@router.post("", response_model=BidRead, status_code=201)
def create_bid(
    payload: BidCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("COMPRADOR")),
) -> BidRead:
    return services.place_bid(db, payload, user)


@router.get("", response_model=list[BidRead])
def list_bids(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("ADMINISTRADOR", "COMPRADOR")),
) -> list[BidRead]:
    return services.list_bids_for_user(db, user, offset=offset, limit=limit)


@router.get("/{bid_id}", response_model=BidRead)
def read_bid(
    bid_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("ADMINISTRADOR", "COMPRADOR")),
) -> BidRead:
    return services.get_bid_for_user(db, bid_id, user)
