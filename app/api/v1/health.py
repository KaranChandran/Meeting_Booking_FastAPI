from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from app.utils.database import check_db_connection
from app.utils.cache import check_redis_connection

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """
    Health check endpoint for load balancer.

    Returns:
    - 200 OK: All systems operational
    - 503 Service Unavailable: Database down

    Response includes:
    - Database connectivity
    - Redis connectivity
    - Application version
    """

    response = {
        "status": "healthy",
        "version": "1.0.0",
        "checks": {}
    }

    http_status = status.HTTP_200_OK

    # ---------------- Database Check (CRITICAL) ----------------
    try:
        db_healthy = await check_db_connection()
        if db_healthy:
            response["checks"]["database"] = "ok"
        else:
            response["checks"]["database"] = "degraded"
            response["status"] = "unhealthy"
            http_status = status.HTTP_503_SERVICE_UNAVAILABLE
    except Exception as exc:
        response["checks"]["database"] = f"error: {exc}"
        response["status"] = "unhealthy"
        http_status = status.HTTP_503_SERVICE_UNAVAILABLE

    # ---------------- Redis Check (NON-CRITICAL) ----------------
    try:
        redis_healthy = await check_redis_connection()
        response["checks"]["redis"] = "ok" if redis_healthy else "degraded"
        if not redis_healthy and response["status"] == "healthy":
            response["status"] = "degraded"
    except Exception as exc:
        response["checks"]["redis"] = f"error: {exc}"
        if response["status"] == "healthy":
            response["status"] = "degraded"

    return JSONResponse(
        content=response,
        status_code=http_status
    )
