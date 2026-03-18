"""Redis connection management."""

import redis.asyncio as redis
from typing import Optional
from common.core.config import settings


class RedisClient:
    """Redis async client wrapper."""

    def __init__(self):
        self._pool: Optional[redis.ConnectionPool] = None
        self._client: Optional[redis.Redis] = None

    async def connect(self) -> redis.Redis:
        """Connect to Redis."""
        if self._client is None:
            self._pool = redis.ConnectionPool.from_url(
                settings.get_redis_url(),
                max_connections=20,
                decode_responses=True,
            )
            self._client = redis.Redis(connection_pool=self._pool)
        return self._client

    async def disconnect(self):
        """Disconnect from Redis."""
        if self._client:
            await self._client.close()
        if self._pool:
            await self._pool.disconnect()
        self._client = None
        self._pool = None

    @property
    def client(self) -> redis.Redis:
        """Get Redis client."""
        if self._client is None:
            raise RuntimeError("Redis not connected. Call connect() first.")
        return self._client


redis_client = RedisClient()


async def get_redis() -> redis.Redis:
    """Get Redis client."""
    return await redis_client.connect()
