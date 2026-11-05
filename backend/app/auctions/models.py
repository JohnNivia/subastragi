"""Auction event entity."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.adjudications.models import Adjudication
    from app.bids.models import Bid


class Auction(Base):
    """Scheduled sale event for one cattle lot."""

    __tablename__ = "eventos_subasta"
    __table_args__ = (
        CheckConstraint("precio_base_kilo > 0", name="precio_base_positivo"),
        CheckConstraint("incremento_minimo_puja > 0", name="incremento_positivo"),
        CheckConstraint("fecha_cierre > fecha_inicio", name="fechas_ordenadas"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    lote_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("lotes_ganado.id", ondelete="RESTRICT"),
        unique=True,
    )
    precio_base_kilo: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    incremento_minimo_puja: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )
    fecha_inicio: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    fecha_cierre: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    estado_subasta: Mapped[str] = mapped_column(
        String(20), nullable=False, default="PROGRAMADA"
    )

    lote = relationship("CattleLot", back_populates="subasta", lazy="joined")
    pujas: Mapped[list["Bid"]] = relationship(back_populates="subasta")
    acta: Mapped["Adjudication | None"] = relationship(
        back_populates="subasta", uselist=False
    )


EventoSubasta = Auction
