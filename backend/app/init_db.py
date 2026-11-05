"""Create the initial schema and required role catalog for development."""

from sqlalchemy import select

from app.adjudications import models as adjudication_models  # noqa: F401
from app.auctions import models as auction_models  # noqa: F401
from app.auth import models as auth_models  # noqa: F401
from app.bids import models as bid_models  # noqa: F401
from app.cattle_lots import models as cattle_models  # noqa: F401
from app.core.database import Base, SessionLocal, engine
from app.users.models import Role

DEFAULT_ROLES = {
    "ADMINISTRADOR": "Administración y auditoría del sistema",
    "GANADERO": "Gestión de lotes y subastas propias",
    "COMPRADOR": "Consulta de subastas, pujas y adjudicaciones propias",
}


def initialize_database() -> None:
    """Create missing tables and insert missing role catalog entries."""
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        existing = set(db.scalars(select(Role.nombre_rol)))
        for name, description in DEFAULT_ROLES.items():
            if name not in existing:
                db.add(Role(nombre_rol=name, descripcion=description))
        db.commit()


if __name__ == "__main__":
    initialize_database()
    print("Esquema y roles inicializados.")
