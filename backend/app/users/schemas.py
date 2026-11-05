"""Strict request and response schemas for accounts and roles."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RoleName(StrEnum):
    """Publicly assignable and administrative roles."""

    ADMINISTRADOR = "ADMINISTRADOR"
    GANADERO = "GANADERO"
    COMPRADOR = "COMPRADOR"


class Schema(BaseModel):
    """Common strict, whitespace-normalizing schema configuration."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class RoleRead(Schema):
    id: int
    nombre_rol: RoleName
    descripcion: str


class UserRead(Schema):
    id: UUID
    email: EmailStr
    nombre_completo: str
    documento_identidad: str
    telefono: str | None
    estado: bool
    fecha_creacion: datetime
    roles: list[RoleRead]

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class UserCreate(Schema):
    email: EmailStr
    password: str = Field(min_length=12, max_length=72)
    nombre_completo: str = Field(min_length=2, max_length=160)
    documento_identidad: str = Field(min_length=5, max_length=40)
    telefono: str | None = Field(default=None, max_length=30)
    rol: RoleName = RoleName.COMPRADOR

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("La contraseña supera el límite de 72 bytes de bcrypt")
        return value


UserResponse = UserRead


class UserProfileUpdate(Schema):
    nombre_completo: str | None = Field(default=None, min_length=2, max_length=160)
    telefono: str | None = Field(default=None, max_length=30)

    @field_validator("nombre_completo")
    @classmethod
    def name_cannot_be_null(cls, value: str | None) -> str | None:
        if value is None:
            raise ValueError("El nombre completo no puede ser nulo")
        return value


class UserAdminUpdate(UserProfileUpdate):
    estado: bool | None = None
    roles: list[RoleName] | None = Field(default=None, min_length=1)


class RoleCreate(Schema):
    nombre_rol: RoleName
    descripcion: str = Field(min_length=3, max_length=200)
