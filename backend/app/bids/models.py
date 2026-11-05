"""Individual auction bids."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Numeric, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.auctions.models import Auction


class Bid(Base):
    """A buyer's per-kilogram offer in an auction."""

    __tablename__ = "pujas_ofertas"

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    subasta_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("eventos_subasta.id", ondelete="RESTRICT"),
        index=True,
    )
    comprador_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("usuarios.id", ondelete="RESTRICT"), index=True
    )
    monto_ofertado_kilo: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    fecha_hora_puja: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    comprador = relationship("User", lazy="joined")
    subasta: Mapped["Auction"] = relationship(back_populates="pujas")


PujaOferta = Bid
