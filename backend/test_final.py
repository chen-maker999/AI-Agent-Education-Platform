#!/usr/bin/env python
"""Final API test."""
import asyncio
import httpx

async def test():
    base_url = 'http://localhost:8000'
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        # Login
        r = await client.post('/api/v1/auth/login', data={'username': 'demo', 'password': 'demo123'})
        token = r.json()['data']['access_token']
        h = {'Authorization': f'Bearer {token}'}
        
        print("=== BASE SERVICES ===")
        tests = [
            ('GET', '/api/v1/auth/me', None),
            ('GET', '/api/v1/roles', None),
            ('GET', '/api/v1/registry/services', None),
            ('GET', '/api/v1/config', None),
            ('GET', '/api/v1/cache/stats', None),
        ]
        for m, p, d in tests:
            try:
                r = await client.get(p, headers=h)
                print(f'{p}: {r.status_code}')
            except Exception as e:
                print(f'{p}: ERROR')
        
        print("\n=== KNOWLEDGE SERVICES ===")
        tests = [
            ('GET', '/api/v1/knowledge/points', None),
            ('GET', '/api/v1/knowledge/graph', None),
            ('GET', '/api/v1/knowledge/vector/stats', None),
            ('GET', '/api/v1/knowledge/chunk', None),
            ('GET', '/api/v1/knowledge/faiss/stats', None),
            ('GET', '/api/v1/knowledge/es/stats', None),
        ]
        for m, p, d in tests:
            try:
                r = await client.get(p, headers=h)
                print(f'{p}: {r.status_code}')
            except Exception as e:
                print(f'{p}: ERROR')
        
        print("\n=== INTELLIGENCE SERVICES ===")
        tests = [
            ('POST', '/api/v1/chat/message', {"student_id": "s1", "message": "hello"}),
            ('GET', '/api/v1/evaluate/weakness/s1', None),
            ('GET', '/api/v1/evaluate/strength/s1', None),
            ('GET', '/api/v1/warning', None),
            ('GET', '/api/v1/warning/stats', None),
        ]
        for m, p, d in tests:
            try:
                if d:
                    r = await client.post(p, json=d, headers=h)
                else:
                    r = await client.get(p, headers=h)
                print(f'{p}: {r.status_code}')
            except Exception as e:
                print(f'{p}: ERROR')
        
        print("\n=== ADAPT SERVICES ===")
        tests = [
            ('GET', '/api/v1/adapt/gateway/platforms', None),
            ('GET', '/api/v1/adapt/sync/jobs', None),
        ]
        for m, p, d in tests:
            try:
                r = await client.get(p, headers=h)
                print(f'{p}: {r.status_code}')
            except Exception as e:
                print(f'{p}: ERROR')
        
        print("\n=== VISUAL SERVICES ===")
        tests = [
            ('GET', '/api/v1/visual/portrait', None),
            ('GET', '/api/v1/visual/error-distribution?course_id=python101', None),
            ('GET', '/api/v1/visual/timeseries?student_id=s1', None),
        ]
        for m, p, d in tests:
            try:
                r = await client.get(p, headers=h)
                print(f'{p}: {r.status_code}')
            except Exception as e:
                print(f'{p}: ERROR')
        
        print("\n=== DATA SERVICES ===")
        tests = [
            ('GET', '/api/v1/collect/status', None),
            ('GET', '/api/v1/homework', None),
            ('GET', '/api/v1/portrait/student_001', None),
            ('GET', '/api/v1/feedback', None),
        ]
        for m, p, d in tests:
            try:
                r = await client.get(p, headers=h)
                print(f'{p}: {r.status_code}')
            except Exception as e:
                print(f'{p}: ERROR')

asyncio.run(test())
