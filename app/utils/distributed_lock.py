import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from http.client import HTTPException

import redis.asyncio as redis


class DistributedLock:
    """
    Redis-based distributed lock for preventing race conditions.

    Usage:
        async with DistributedLock("booking:slot:2025-12-15:14:30").acquire():
            # Critical section: check slot and create booking
            pass

    Implementation Notes:
    - Uses Redis SET with NX (set if not exists) and EX (expiry)
    - Lock expires after 5 seconds to prevent deadlocks
    - Implements retry logic with exponential backoff
    """

    def __init__(self, lock_key: str, timeout_seconds: int = 5):
        self.lock_key = f"lock:{lock_key}"
        self.timeout = timeout_seconds
        self.redis_client = redis.Redis.from_url("redis://localhost:6379")
        self.lock_value = None

    @asynccontextmanager
    async def acquire(self, retry_times: int = 3):
        """
        Acquire distributed lock with retry.

        Args:
            retry_times: Number of retry attempts

        Raises:
            RuntimeError: Failed to acquire lock after retries
        """
        acquired = False

        for attempt in range(retry_times):
            # Generate unique lock value (prevents accidental unlock)
            self.lock_value = str(datetime.utcnow().timestamp())

            # Try to acquire lock
            acquired = await self.redis_client.set(
                self.lock_key,
                self.lock_value,
                nx=True,          # Only set if not exists
                ex=self.timeout   # Expiry in seconds
            )

            if acquired:
                break

            # Exponential backoff
            wait_time = 0.1 * (2 ** attempt)
            await asyncio.sleep(wait_time)

        if not acquired:
            raise RuntimeError(f"Failed to acquire lock: {self.lock_key}")

        try:
            yield
        finally:
            # Release lock only if we still own it
            lua_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
            """

            await self.redis_client.eval(
                lua_script,
                1,
                self.lock_key,
                self.lock_value
            )


# Usage in booking service
async def create_booking_with_lock(booking_data, repository):
    lock_key = f"booking:slot:{booking_data.date}:{booking_data.time}"

    async with DistributedLock(lock_key).acquire():
        # Check if slot is available
        existing = await repository.find_by_date_time(
            booking_data.date,
            booking_data.time
        )

        if existing:
            raise HTTPException(
                status_code=400,
                detail="Slot already booked"
            )

        # Create booking
        new_booking = await repository.create(booking_data)
        return new_booking
