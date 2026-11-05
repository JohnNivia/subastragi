"""Centralized API exception translation and sanitized error responses."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger("subastagro")


def register_exception_handlers(app: FastAPI) -> None:
    """Register application-wide error handlers on the FastAPI application."""

    @app.exception_handler(IntegrityError)
    async def handle_integrity_error(_: Request, exc: IntegrityError) -> JSONResponse:
        logger.info(
            "Database integrity constraint rejected a request: %s",
            type(exc.orig).__name__,
        )
        return JSONResponse(
            status_code=409,
            content={"detail": "El recurso entra en conflicto con datos existentes"},
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        _: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = [
            {"loc": error["loc"], "msg": error["msg"], "type": error["type"]}
            for error in exc.errors()
        ]
        return JSONResponse(status_code=422, content={"detail": errors})

    @app.exception_handler(Exception)
    async def handle_unexpected_error(_: Request, _exc: Exception) -> JSONResponse:
        logger.exception("Unhandled application error")
        return JSONResponse(
            status_code=500,
            content={"detail": "Error interno del servidor"},
        )
