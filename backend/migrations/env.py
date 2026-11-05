"""Alembic environment using the application's SQLAlchemy metadata."""

from alembic import context
from app.adjudications import models as adjudication_models  # noqa: F401
from app.auctions import models as auction_models  # noqa: F401
from app.auth import models as auth_models  # noqa: F401
from app.bids import models as bid_models  # noqa: F401
from app.cattle_lots import models as cattle_models  # noqa: F401
from app.core.config import settings
from app.core.database import Base
from app.users import models as user_models  # noqa: F401
from sqlalchemy import engine_from_config, pool

config = context.config
target_metadata = Base.metadata
database_url = settings.sqlalchemy_database_url
config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))


def run_migrations_offline() -> None:
    """Run migrations using SQL statements generated from the configured URL."""
    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations using a live database connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    try:
        with connectable.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                compare_type=True,
            )
            with context.begin_transaction():
                context.run_migrations()
    finally:
        connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
