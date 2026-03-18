#!/usr/bin/env python
"""Test database connections and create tables."""
import asyncio
import sys

# Add backend to path
sys.path.insert(0, r"D:\AI-Agent-Education-Platform-cursor\backend")

async def test_and_setup():
    from sqlalchemy import text
    from common.database.postgresql import AsyncSessionLocal
    from common.core.config import settings
    
    print("=" * 60)
    print("Testing Database Connections")
    print("=" * 60)
    
    # Test PostgreSQL
    print("\n1. PostgreSQL Connection:")
    print(f"   Host: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}")
    print(f"   Database: {settings.POSTGRES_DB}")
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"   ✓ Connected! Version: {version[:50]}...")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test Redis
    print("\n2. Redis Connection:")
    print(f"   Host: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    try:
        import redis.asyncio as redis
        r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)
        await r.ping()
        print("   ✓ Connected!")
        await r.close()
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test Neo4j
    print("\n3. Neo4j Connection:")
    print(f"   Host: {settings.NEO4J_HOST}:{settings.NEO4J_PORT}")
    try:
        from neo4j import AsyncGraphDatabase
        driver = AsyncGraphDatabase.driver(
            f"bolt://{settings.NEO4J_HOST}:{settings.NEO4J_PORT}",
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
        await driver.verify_connectivity()
        print("   ✓ Connected!")
        await driver.close()
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test MinIO
    print("\n4. MinIO Connection:")
    print(f"   Host: {settings.MINIO_ENDPOINT}")
    try:
        from minio import Minio
        client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False
        )
        buckets = client.list_buckets()
        print(f"   ✓ Connected! Buckets: {[b.name for b in buckets]}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test Elasticsearch
    print("\n5. Elasticsearch Connection:")
    print(f"   Host: {settings.ELASTICSEARCH_HOST}:{settings.ELASTICSEARCH_PORT}")
    try:
        from elasticsearch import Elasticsearch
        client = Elasticsearch([f"http://{settings.ELASTICSEARCH_HOST}:{settings.ELASTICSEARCH_PORT}"])
        info = client.info()
        print(f"   ✓ Connected! Version: {info['version']['number']}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_and_setup())
