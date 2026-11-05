"""Bid creation and history response schemas."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import ConfigDict, Field

from app.users.schemas import Schema


class BidCreate(Schema):
    subasta_id: UUID
    monto_ofertado_kilo: Decimal = Field(gt=0, max_digits=12, decimal_places=2)


class BidRead(Schema):
    id: UUID
    subasta_id: UUID
    comprador_id: UUID
    monto_ofertado_kilo: Decimal
    fecha_hora_puja: datetime

    model_config = ConfigDict(from_attributes=True, extra="forbid")


BidResponse = BidRead
