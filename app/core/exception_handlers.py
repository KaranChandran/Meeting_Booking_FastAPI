from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse


async def http_exception_handler(
    request: Request,
    exc: HTTPException,
):
    if isinstance(exc.detail, dict):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                **exc.detail,
                "meta": {"request_id": "generated-at-runtime"},
            },
        )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "error": {
                "code": "HTTP_EXCEPTION",
                "message": exc.detail,
            },
        },
    )
