"""Create the first administrator from explicit environment variables."""

import os
from uuid import uuid4

from pydantic import EmailStr, TypeAdapter, ValidationError
from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.users.models import Role, User


def create_admin() -> None:
    raw_email = os.environ.get("BOOTSTRAP_ADMIN_EMAIL", "").strip()
    password = os.environ.get("BOOTSTRAP_ADMIN_PASSWORD", "")
    if not raw_email or not password:
        raise SystemExit(
            "Define BOOTSTRAP_ADMIN_EMAIL y BOOTSTRAP_ADMIN_PASSWORD para continuar."
        )
    try:
        email = str(TypeAdapter(EmailStr).validate_python(raw_email)).lower()
    except ValidationError:
        raise SystemExit("BOOTSTRAP_ADMIN_EMAIL debe ser un correo válido.") from None
    if len(password) < 12 or len(password.encode("utf-8")) > 72:
        raise SystemExit(
            "La contraseña debe tener entre 12 caracteres y 72 bytes UTF-8."
        )

    with SessionLocal() as db:
        if db.scalar(select(User.id).where(User.email == email)):
            raise SystemExit("Ya existe una cuenta con ese correo.")
        role = db.scalar(select(Role).where(Role.nombre_rol == "ADMINISTRADOR"))
        if role is None:
            raise SystemExit("Inicializa primero el esquema con python -m app.init_db.")
        user = User(
            email=email,
            password_hash=hash_password(password),
            nombre_completo="Administrador SubastAgro",
            documento_identidad=f"BOOTSTRAP-{uuid4().hex}",
            estado=True,
            roles=[role],
        )
        db.add(user)
        db.commit()
    print("Administrador creado.")


if __name__ == "__main__":
    create_admin()
