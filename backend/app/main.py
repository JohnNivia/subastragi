"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.adjudications import models as adjudication_models  # noqa: F401
from app.adjudications.routes import router as adjudications_router
from app.auctions import models as auction_models  # noqa: F401
from app.auctions.routes import router as auctions_router
from app.auth import models as auth_models  # noqa: F401
from app.auth.routes import router as auth_router
from app.bids import models as bid_models  # noqa: F401
from app.bids.routes import router as bids_router
from app.cattle_lots import models as cattle_models  # noqa: F401
from app.cattle_lots.routes import router as cattle_router
from app.core.config import settings
from app.core.database import engine
from app.core.exceptions import register_exception_handlers
from app.core.middleware import security_headers_middleware
from app.users import models as user_models  # noqa: F401
from app.users.routes import router as users_router

logger = logging.getLogger("subastagro")


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Keep schema lifecycle explicit; deployments initialize via app.init_db."""
    yield
    engine.dispose()


app = FastAPI(
    title="SubastAgro API",
    description="API REST para la gestión segura de subastas de ganado vacuno.",
    version="1.0.0",
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
    openapi_url="/openapi.json" if settings.environment != "production" else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)
app.middleware("http")(security_headers_middleware)


register_exception_handlers(app)


@app.get("/health/live", tags=["Sistema"])
def liveness() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/health", tags=["Sistema"])
def api_health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready", tags=["Sistema"])
def readiness() -> dict[str, str]:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        logger.warning("Database readiness probe failed: %s", type(exc).__name__)
        raise HTTPException(
            status_code=503, detail="Base de datos no disponible"
        ) from None
    return {"status": "ready"}


for router in (
    auth_router,
    users_router,
    cattle_router,
    auctions_router,
    bids_router,
    adjudications_router,
):
    app.include_router(router, prefix="/api/v1")
