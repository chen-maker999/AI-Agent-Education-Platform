"""Neo4j connection management."""

from neo4j import AsyncGraphDatabase, Driver
from typing import Optional
from common.core.config import settings


class Neo4jClient:
    """Neo4j async client wrapper."""

    def __init__(self):
        self._driver: Optional[Driver] = None

    async def connect(self) -> Driver:
        """Connect to Neo4j."""
        if self._driver is None:
            self._driver = AsyncGraphDatabase.driver(
                settings.get_neo4j_url(),
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
                max_connection_lifetime=3600,
                max_connection_pool_size=50,
            )
        return self._driver

    async def close(self):
        """Close Neo4j connection."""
        if self._driver:
            await self._driver.close()
            self._driver = None

    async def verify_connectivity(self) -> bool:
        """Verify Neo4j connectivity."""
        if self._driver is None:
            await self.connect()
        try:
            async with self._driver.session() as session:
                await session.run("RETURN 1")
            return True
        except Exception:
            return False

    @property
    def driver(self) -> Driver:
        """Get Neo4j driver."""
        if self._driver is None:
            raise RuntimeError("Neo4j not connected. Call connect() first.")
        return self._driver


neo4j_client = Neo4jClient()


async def get_neo4j() -> Driver:
    """Get Neo4j driver."""
    return await neo4j_client.connect()
