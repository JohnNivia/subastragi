"""Auction scheduling and response schemas."""

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import ConfigDict, Field, model_validator

from app.users.schemas import Schema


class AuctionStatus(StrEnum):
    PROGRAMADA = "PROGRAMADA"
    ACTIVA = "ACTIVA"
    FINALIZADA = "FINALIZADA"
    DESIERTA = "DESIERTA"


EstadoSubasta = AuctionStatus


class AuctionCreate(Schema):
    lote_id: UUID
    precio_base_kilo: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    incremento_minimo_puja: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    fecha_inicio: datetime
    fecha_cierre: datetime

    @model_validator(mode="after")
    def validate_dates(self) -> "AuctionCreate":
        if self.fecha_inicio.tzinfo is None or self.fecha_cierre.tzinfo is None:
            raise ValueError("Las fechas deben incluir zona horaria")
        if self.fecha_cierre <= self.fecha_inicio:
            raise ValueError("La fecha de cierre debe ser posterior al inicio")
        return self


class AuctionUpdate(Schema):
    precio_base_kilo: Decimal | None = Field(
        default=None, gt=0, max_digits=12, decimal_places=2
    )
    incremento_minimo_puja: Decimal | None = Field(
        default=None, gt=0, max_digits=12, decimal_places=2
    )
    fecha_inicio: datetime | None = None
    fecha_cierre: datetime | None = None

    @model_validator(mode="after")
    def validate_changes(self) -> "AuctionUpdate":
        for field in (
            "precio_base_kilo",
            "incremento_minimo_puja",
            "fecha_inicio",
            "fecha_cierre",
        ):
            value = getattr(self, field)
            if field in self.model_fields_set and value is None:
                raise ValueError(f"{field} no puede ser nulo")
            if (
                field.startswith("fecha_")
                and value is not None
                and value.tzinfo is None
            ):
                raise ValueError("Las fechas deben incluir zona horaria")
        return self


class AuctionRead(Schema):
    id: UUID
    lote_id: UUID
    precio_base_kilo: Decimal
    incremento_minimo_puja: Decimal
    fecha_inicio: datetime
    fecha_cierre: datetime
    estado_subasta: AuctionStatus

    model_config = ConfigDict(from_attributes=True, extra="forbid")


AuctionResponse = AuctionRead
