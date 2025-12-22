import redis
from app.core.config import settings

async def check_redis_connection() -> bool:
    """
    Check Redis connectivity.
    Returns True if Redis is reachable, else False.
    """
    try:
        r = redis.Redis.from_url(
            settings.REDIS_URL,
            socket_connect_timeout=2
        )
        return r.ping()
    except Exception:
        return False
