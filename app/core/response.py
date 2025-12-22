from uuid import uuid4
from typing import Any, Optional


def success_response(
    data: Any,
    idempotency_key: Optional[str] = None,
):
    return {
        "status": "success",
        "data": data,
        "meta": {
            "request_id": f"req-{uuid4()}",
            "idempotency_key": idempotency_key,
        },
    }


def error_response(
    code: str,
    message: str,
    details: dict | None = None,
):
    return {
        "status": "error",
        "error": {
            "code": code,
            "message": message,
            "details": details,
        },
    }
