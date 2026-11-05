"""Adjudication response schema."""

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import ConfigDict

from app.users.schemas import Schema


class AdjudicationRead(Schema):
    id: UUID
    subasta_id: UUID
    comprador_ganador_id: UUID
    puja_ganadora_id: UUID
    monto_total_final: Decimal
    guia_movilizacion_codigo: str
    estado_pago: str
    fecha_cierre: datetime

    model_config = ConfigDict(from_attributes=True, extra="forbid")


AdjudicationResponse = AdjudicationRead


class PaymentStatus(StrEnum):
    PENDIENTE = "PENDIENTE"
    PAGADO = "PAGADO"
    RECHAZADO = "RECHAZADO"


class AdjudicationPaymentUpdate(Schema):
    estado_pago: PaymentStatus
