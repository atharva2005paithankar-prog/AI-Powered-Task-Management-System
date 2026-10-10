"""Turns Python exceptions into clean JSON error responses."""
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from app.exceptions import AppError

logger = logging.getLogger(__name__)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError):
        # Covers our own errors: 401, 403, 404, 409 and every AI error (502/503/504).
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    @app.exception_handler(SQLAlchemyError)
    async def handle_database_error(request: Request, exc: SQLAlchemyError):
        # Log the real error for developers, but never show it to the client.
        logger.exception("Database error on %s %s", request.method, request.url.path)
        if isinstance(exc, OperationalError):
            return JSONResponse(
                status_code=503,
                content={"detail": "The database is unavailable. Please try again later."},
            )
        return JSONResponse(status_code=500, content={"detail": "A database error occurred."})
