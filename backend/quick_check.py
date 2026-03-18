#!/usr/bin/env python
"""Quick API status check."""
import asyncio
import httpx

async def check():
    base_url = 'http://localhost:8000'
    async with httpx.AsyncClient(base_url=base_url, timeout=10.0) as client:
        # Login
        r = await client.post('/api/v1/auth/login', data={'username': 'demo', 'password': 'demo123'})
        token = r.json()['data']['access_token']
        h = {'Authorization': f'Bearer {token}'}
        
        paths = [
            "/api/v1/auth/me", "/api/v1/roles", "/api/v1/registry/services",
            "/api/v1/cache/stats", "/api/v1/knowledge/points", "/api/v1/knowledge/graph",
            "/api/v1/knowledge/vector/stats", "/api/v1/knowledge/chunk",
            "/api/v1/knowledge/faiss/stats", "/api/v1/knowledge/es/stats",
            "/api/v1/chat/message", "/api/v1/warning", "/api/v1/warning/stats",
            "/api/v1/adapt/gateway/platforms", "/api/v1/adapt/sync/jobs",
            "/api/v1/visual/portrait", "/api/v1/visual/error-distribution?course_id=c1",
            "/api/v1/collect/status", "/api/v1/homework", "/api/v1/portrait/student_001",
            "/api/v1/feedback", "/api/v1/rag/chat", "/api/v1/rag/documents",
            "/api/v1/evaluate/weakness/s1", "/api/v1/evaluate/strength/s1",
            "/api/v1/exercise/generate", "/api/v1/parse/text",
        ]
        
        ok, fail = [], []
        for p in paths:
            try:
                r = await client.get(p, headers=h)
                (ok if r.status_code < 400 else fail).append(f"{p}: {r.status_code}")
            except:
                fail.append(f"{p}: ERROR")
        
        print(f"✅ 正常: {len(ok)}")
        for x in ok: print(f"  ✓ {x}")
        print(f"\n❌ 异常: {len(fail)}")
        for x in fail: print(f"  ✗ {x}")

asyncio.run(check())
