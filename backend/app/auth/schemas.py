"""Authentication request and token response schemas."""

from pydantic import EmailStr, Field, field_validator

from app.users.schemas import Schema, UserCreate, UserRead


class RegisterRequest(UserCreate):
    """Authentication endpoint schema for public account creation."""


class LoginRequest(Schema):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class PasswordChangeRequest(Schema):
    current_password: str = Field(min_length=1, max_length=72)
    new_password: str = Field(min_length=12, max_length=72)

    @field_validator("new_password")
    @classmethod
    def new_password_fits_bcrypt(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("La contraseña supera el límite de 72 bytes de bcrypt")
        return value


class TokenResponse(Schema):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    usuario: UserRead


class LogoutResponse(Schema):
    mensaje: str = "Sesión cerrada"
