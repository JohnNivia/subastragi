"""Cattle breed and lot entities."""

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Float,
    ForeignKey,
    Integer,
    String,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.auctions.models import Auction


class Breed(Base):
    """Breed catalog with intended livestock purpose."""

    __tablename__ = "razas_ganado"

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    nombre_raza: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    proposito: Mapped[str] = mapped_column(String(40), nullable=False)
    estado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class CattleLot(Base):
    """A seller-owned, uniquely coded lot of cattle."""

    __tablename__ = "lotes_ganado"
    __table_args__ = (
        CheckConstraint("cantidad_cabezas > 0", name="cantidad_positiva"),
        CheckConstraint("peso_promedio_kg > 0", name="peso_positivo"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    ganadero_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("usuarios.id", ondelete="RESTRICT"), index=True
    )
    raza_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("razas_ganado.id", ondelete="RESTRICT"),
        index=True,
    )
    codigo_lote: Mapped[str] = mapped_column(
        String(40), unique=True, index=True, nullable=False
    )
    cantidad_cabezas: Mapped[int] = mapped_column(Integer, nullable=False)
    peso_promedio_kg: Mapped[float] = mapped_column(Float, nullable=False)
    vacunacion_al_dia: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    ubicacion_hacienda: Mapped[str] = mapped_column(String(180), nullable=False)
    estado_lote: Mapped[str] = mapped_column(
        String(24), nullable=False, default="DISPONIBLE"
    )

    ganadero = relationship("User", lazy="joined")
    raza: Mapped[Breed] = relationship(lazy="joined")
    subasta: Mapped["Auction | None"] = relationship(
        back_populates="lote", uselist=False
    )


RazaGanado = Breed
LoteGanado = CattleLot
