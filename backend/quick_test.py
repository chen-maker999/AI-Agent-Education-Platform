#!/usr/bin/env python
"""Quick API test."""
import asyncio
import httpx

async def test():
    base_url = 'http://localhost:8000'
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        # Login
        r = await client.post('/api/v1/auth/login', data={'username': 'demo', 'password': 'demo123'})
        token = r.json()['data']['access_token']
        h = {'Authorization': f'Bearer {token}'}
        
        # Test key endpoints
        tests = [
            ('GET', '/api/v1/auth/me'),
            ('GET', '/api/v1/knowledge/points'),
            ('GET', '/api/v1/knowledge/graph'),
            ('GET', '/api/v1/collect/status'),
            ('GET', '/api/v1/feedback'),
            ('GET', '/api/v1/warning'),
            ('GET', '/api/v1/adapt/gateway/platforms'),
            ('GET', '/api/v1/visual/portrait'),
        ]
        for m, p in tests:
            r = await client.get(p, headers=h)
            print(f'{p}: {r.status_code}')

asyncio.run(test())
