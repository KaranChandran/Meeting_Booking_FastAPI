import sqlite3
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.logging import logger


async def global_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "unknown")

    if isinstance(exc, RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "status": "error",
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": exc.errors(),
                },
                "meta": {"request_id": request_id},
            },
        )

    if isinstance(exc, sqlite3.IntegrityError):
        logger.warning(f"Integrity error: {exc}")
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "status": "error",
                "error": {
                    "code": "CONSTRAINT_VIOLATION",
                    "message": "Database constraint violation",
                },
                "meta": {"request_id": request_id},
            },
        )

    if isinstance(exc, sqlite3.OperationalError):
        logger.error(f"Database error: {exc}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "error",
                "error": {
                    "code": "SERVICE_UNAVAILABLE",
                    "message": "Database unavailable",
                },
                "meta": {"request_id": request_id},
            },
        )

    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "Unexpected error occurred",
            },
            "meta": {"request_id": request_id},
        },
    )
