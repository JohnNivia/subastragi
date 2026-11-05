"""Auction scheduling and catalog endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auctions import services
from app.auctions.schemas import AuctionCreate, AuctionRead, AuctionUpdate
from app.core.database import get_db
from app.core.dependencies import require_roles
from app.users.models import User

router = APIRouter(prefix="/auctions", tags=["Subastas"])


@router.get("", response_model=list[AuctionRead])
def list_auctions(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("ADMINISTRADOR", "GANADERO", "COMPRADOR")),
) -> list[AuctionRead]:
    return services.list_auctions_for_user(db, user, offset=offset, limit=limit)


@router.post("", response_model=AuctionRead, status_code=201)
def create_auction(
    payload: AuctionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("ADMINISTRADOR", "GANADERO")),
) -> AuctionRead:
    return services.schedule_auction_for_user(db, payload, user)


@router.patch("/{auction_id}", response_model=AuctionRead)
def update_auction(
    auction_id: UUID,
    payload: AuctionUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("ADMINISTRADOR", "GANADERO")),
) -> AuctionRead:
    return services.update_auction_for_user(db, auction_id, user, payload)


@router.get("/{auction_id}", response_model=AuctionRead)
def read_auction(
    auction_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("ADMINISTRADOR", "GANADERO", "COMPRADOR")),
) -> AuctionRead:
    return services.get_auction_for_user(db, auction_id, user)
