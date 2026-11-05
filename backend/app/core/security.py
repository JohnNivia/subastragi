"""Password hashing and signed access/refresh JWT helpers."""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password with bcrypt, enforcing its 72-byte input limit."""
    if len(password.encode("utf-8")) > 72:
        raise ValueError("La contraseña no puede superar 72 bytes UTF-8")
    return password_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Compare a candidate password with its stored bcrypt hash."""
    if len(plain_password.encode("utf-8")) > 72:
        return False
    return password_context.verify(plain_password, password_hash)


def create_access_token(user_id: UUID, roles: list[str]) -> str:
    """Create a short-lived access token carrying the current role claims."""
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "roles": roles,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
        "jti": str(uuid4()),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(user_id: UUID, token_id: UUID) -> str:
    """Create a refresh JWT whose identifier is persisted for revocation."""
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(days=settings.refresh_token_expire_days),
        "jti": str(token_id),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> dict[str, object] | None:
    """Decode a signed JWT, returning None for invalid or expired tokens."""
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        return None
