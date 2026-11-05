"""Legal and financial auction adjudication record."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Adjudication(Base):
    """Winning bid, final amount, and movement-guide record."""

    __tablename__ = "actas_adjudicacion"

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    subasta_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("eventos_subasta.id", ondelete="RESTRICT"),
        unique=True,
    )
    comprador_ganador_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("usuarios.id", ondelete="RESTRICT")
    )
    puja_ganadora_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("pujas_ofertas.id", ondelete="RESTRICT"),
        unique=True,
    )
    monto_total_final: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    guia_movilizacion_codigo: Mapped[str] = mapped_column(
        String(48), unique=True, nullable=False
    )
    estado_pago: Mapped[str] = mapped_column(
        String(20), nullable=False, default="PENDIENTE"
    )
    fecha_cierre: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    subasta = relationship("Auction", back_populates="acta", lazy="joined")
    comprador_ganador = relationship("User", lazy="joined")


ActaAdjudicacion = Adjudication
