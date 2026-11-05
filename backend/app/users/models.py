"""User, role, and many-to-many role assignment entities."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

usuario_roles = Table(
    "usuario_roles",
    Base.metadata,
    Column(
        "usuario_id",
        Uuid(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "rol_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True
    ),
)


class User(Base):
    """Account and contact details for an application user."""

    __tablename__ = "usuarios"

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    email: Mapped[str] = mapped_column(
        String(254), unique=True, index=True, nullable=False
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    nombre_completo: Mapped[str] = mapped_column(String(160), nullable=False)
    documento_identidad: Mapped[str] = mapped_column(
        String(40), unique=True, nullable=False
    )
    telefono: Mapped[str | None] = mapped_column(String(30))
    estado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    roles: Mapped[list["Role"]] = relationship(
        secondary=usuario_roles, back_populates="usuarios", lazy="selectin"
    )


class Role(Base):
    """System role catalog entry."""

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre_rol: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    descripcion: Mapped[str] = mapped_column(String(200), nullable=False)

    usuarios: Mapped[list[User]] = relationship(
        secondary=usuario_roles, back_populates="roles"
    )


Usuario = User
Rol = Role
