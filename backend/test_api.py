#!/usr/bin/env python
"""Complete API test - all endpoints."""
import asyncio
import httpx
import json

async def test():
    base_url = 'http://localhost:8000'
    async with httpx.AsyncClient(base_url=base_url, timeout=60.0) as client:
        # Login
        r = await client.post('/api/v1/auth/login', data={'username': 'demo', 'password': 'demo123'})
        if r.status_code != 200:
            print("Login failed!")
            return
        token = r.json()['data']['access_token']
        h = {'Authorization': f'Bearer {token}'}
        
        # Test endpoints
        tests = [
            # BASE SERVICES
            ("GET", "/api/v1/auth/me", None, "auth_me"),
            ("GET", "/api/v1/roles", None, "roles"),
            ("GET", "/api/v1/registry/services", None, "registry"),
            ("GET", "/api/v1/cache/stats", None, "cache"),
            
            # KNOWLEDGE
            ("GET", "/api/v1/knowledge/points", None, "kp_list"),
            ("GET", "/api/v1/knowledge/graph", None, "kg"),
            ("GET", "/api/v1/knowledge/vector/stats", None, "vector"),
            ("GET", "/api/v1/knowledge/chunk", None, "chunk"),
            ("GET", "/api/v1/knowledge/faiss/stats", None, "faiss"),
            ("GET", "/api/v1/knowledge/es/stats", None, "es"),
            
            # INTELLIGENCE
            ("POST", "/api/v1/chat/message", {"student_id": "s1", "message": "hello"}, "chat"),
            ("GET", "/api/v1/warning", None, "warning"),
            ("GET", "/api/v1/warning/stats", None, "warning_stats"),
            ("GET", "/api/v1/evaluate/weakness/s1", None, "eval_weakness"),
            ("GET", "/api/v1/evaluate/strength/s1", None, "eval_strength"),
            
            # DATA
            ("GET", "/api/v1/collect/status", None, "collect"),
            ("GET", "/api/v1/homework", None, "homework"),
            ("GET", "/api/v1/portrait/student_001", None, "portrait"),
            ("GET", "/api/v1/feedback", None, "feedback"),
            ("GET", "/api/v1/timeseries/query?table=test&limit=10", None, "timeseries"),
            
            # ADAPT
            ("GET", "/api/v1/adapt/gateway/platforms", None, "adapt"),
            
            # VISUAL
            ("GET", "/api/v1/visual/portrait", None, "visual_portrait"),
            ("GET", "/api/v1/visual/error-distribution?course_id=c1", None, "visual_errors"),
            
            # RAG
            ("POST", "/api/v1/rag/chat", {"session_id": "s1", "student_id": "st1", "message": "hello"}, "rag"),
            ("GET", "/api/v1/rag/documents", None, "rag_docs"),
        ]
        
        ok, fail = [], []
        
        for method, path, data, name in tests:
            try:
                if method == "GET":
                    r = await client.get(path, headers=h, timeout=30.0)
                else:
                    r = await client.post(path, json=data, headers=h, timeout=30.0)
                
                status = "PASS" if r.status_code < 400 else f"FAIL({r.status_code})"
                if r.status_code < 400:
                    ok.append(f"{name}: {r.status_code}")
                else:
                    fail.append(f"{name}: {r.status_code}")
            except Exception as e:
                fail.append(f"{name}: ERROR")
        
        print("=" * 60)
        print("OK - Working endpoints:")
        print("=" * 60)
        for x in ok:
            print(f"  [OK] {x}")
        
        print(f"\nTotal OK: {len(ok)}")
        
        print("\n" + "=" * 60)
        print("FAIL - Not working endpoints:")
        print("=" * 60)
        for x in fail:
            print(f"  [X] {x}")
        
        print(f"\nTotal FAIL: {len(fail)}")

asyncio.run(test())
