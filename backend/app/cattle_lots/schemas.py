"""Breed and cattle-lot request/response schemas."""

from uuid import UUID

from pydantic import ConfigDict, Field, model_validator

from app.users.schemas import Schema


class BreedCreate(Schema):
    nombre_raza: str = Field(min_length=2, max_length=80)
    proposito: str = Field(min_length=2, max_length=40)


class BreedUpdate(Schema):
    nombre_raza: str | None = Field(default=None, min_length=2, max_length=80)
    proposito: str | None = Field(default=None, min_length=2, max_length=40)
    estado: bool | None = None

    @model_validator(mode="after")
    def reject_null_values(self) -> "BreedUpdate":
        for field in ("nombre_raza", "proposito", "estado"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} no puede ser nulo")
        return self


class BreedRead(Schema):
    id: UUID
    nombre_raza: str
    proposito: str
    estado: bool

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class CattleLotCreate(Schema):
    raza_id: UUID
    codigo_lote: str = Field(min_length=3, max_length=40, pattern=r"^[A-Za-z0-9_-]+$")
    cantidad_cabezas: int = Field(gt=0, le=100_000)
    peso_promedio_kg: float = Field(gt=0, le=2_000)
    vacunacion_al_dia: bool = True
    ubicacion_hacienda: str = Field(min_length=2, max_length=180)


class CattleLotUpdate(Schema):
    raza_id: UUID | None = None
    cantidad_cabezas: int | None = Field(default=None, gt=0, le=100_000)
    peso_promedio_kg: float | None = Field(default=None, gt=0, le=2_000)
    vacunacion_al_dia: bool | None = None
    ubicacion_hacienda: str | None = Field(default=None, min_length=2, max_length=180)

    @model_validator(mode="after")
    def reject_null_values(self) -> "CattleLotUpdate":
        for field in (
            "raza_id",
            "cantidad_cabezas",
            "peso_promedio_kg",
            "vacunacion_al_dia",
            "ubicacion_hacienda",
        ):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} no puede ser nulo")
        return self


class CattleLotStatusUpdate(Schema):
    estado_lote: str = Field(pattern=r"^(DISPONIBLE|SUSPENDIDO)$")


class CattleLotRead(Schema):
    id: UUID
    ganadero_id: UUID
    raza_id: UUID
    codigo_lote: str
    cantidad_cabezas: int
    peso_promedio_kg: float
    vacunacion_al_dia: bool
    ubicacion_hacienda: str
    estado_lote: str

    model_config = ConfigDict(from_attributes=True, extra="forbid")


CattleLotResponse = CattleLotRead
