import hashlib
import json
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.services.idempotency_service import IdempotencyService


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle idempotency for POST, PUT, PATCH, DELETE requests.

    Implementation Notes:
    1. Extract X-Idempotency-Key from headers
    2. For mutating operations, check if key exists in store
    3. If exists, return cached response (status code + body)
    4. If not exists, proceed with request and store result
    5. Set TTL to 24 hours for idempotency keys
    """

    IDEMPOTENT_METHODS = ["POST", "PUT", "PATCH", "DELETE"]

    async def dispatch(self, request: Request, call_next: Callable):
        if request.method not in self.IDEMPOTENT_METHODS:
            return await call_next(request)

        if not request.url.path.startswith("/api/v1/bookings"):
            return await call_next(request)

        idempotency_key = request.headers.get("X-Idempotency-Key")
        if not idempotency_key:
            return Response(
                content=json.dumps({
                    "status": "error",
                    "error": {
                        "code": "MISSING_IDEMPOTENCY_KEY",
                        "message": "X-Idempotency-Key header required"
                    }
                }),
                status_code=400,
                media_type="application/json"
            )

        body = await request.body()
        request._body = body

        request_hash = hashlib.sha256(
            f"{request.method}:{request.url.path}:{body.decode('utf-8', errors='ignore')}".encode()
        ).hexdigest()

        idempotency_service = IdempotencyService()
        cached_response = await idempotency_service.get_response(
            idempotency_key,
            request_hash
        )

        if cached_response:
            return Response(
                content=cached_response["body"],
                status_code=cached_response["status_code"],
                media_type="application/json",
                headers={"X-Idempotent-Replay": "true"}
            )

        response = await call_next(request)

        if 200 <= response.status_code < 300:
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk

            await idempotency_service.store_response(
                idempotency_key,
                request_hash,
                response.status_code,
                response_body.decode("utf-8", errors="ignore"),
                86400
            )

            return Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
        return response
