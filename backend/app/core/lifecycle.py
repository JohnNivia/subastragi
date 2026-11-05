"""Background maintenance for auction state transitions and closeout."""

import asyncio
import logging
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError

from app.adjudications.services import close_auction
from app.auctions.models import Auction
from app.core.database import SessionLocal

logger = logging.getLogger("subastagro")


def _process_auction_lifecycle() -> None:
    """Activate due auctions and close expired auctions."""
    now = datetime.now(UTC)
    with SessionLocal() as db:
        db.execute(
            update(Auction)
            .where(
                Auction.estado_subasta == "PROGRAMADA",
                Auction.fecha_inicio <= now,
                Auction.fecha_cierre > now,
            )
            .values(estado_subasta="ACTIVA")
        )
        expired_ids = list(
            db.scalars(
                select(Auction.id).where(
                    Auction.estado_subasta.in_(("PROGRAMADA", "ACTIVA")),
                    Auction.fecha_cierre <= now,
                )
            )
        )
        db.commit()

    for auction_id in expired_ids:
        with SessionLocal() as db:
            try:
                close_auction(db, auction_id)
            except HTTPException as exc:
                if (
                    exc.status_code != 400
                    or exc.detail != "La subasta ya fue cerrada"
                ):
                    raise
                logger.info(
                    "Auction %s was closed concurrently by another worker",
                    auction_id,
                )


async def run_auction_lifecycle(stop_event: asyncio.Event) -> None:
    """Run periodic auction maintenance until the application shuts down."""
    while not stop_event.is_set():
        try:
            await asyncio.to_thread(_process_auction_lifecycle)
        except SQLAlchemyError:
            logger.exception("Auction lifecycle maintenance failed")
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=15)
        except TimeoutError:
            pass
