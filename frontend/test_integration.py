#!/usr/bin/env python
"""Test frontend and backend integration."""
import sys
import os
import asyncio
import httpx
import json

sys.path.insert(0, r"D:\AI-Agent-Education-Platform-cursor\backend")
os.environ.setdefault("PYTHONPATH", r"D:\AI-Agent-Education-Platform-cursor\backend")

async def test_integration():
    """Test frontend and backend integration."""
    base_url = "http://localhost:8000"
    frontend_url = "http://localhost:5173"
    
    # Check backend
    print("=== Testing Backend ===")
    async with httpx.AsyncClient(base_url=base_url, timeout=10.0) as client:
        response = await client.get("/health")
        print(f"Backend /health: {response.status_code}")
        
        # Login
        response = await client.post("/api/v1/auth/login", data={"username": "demo", "password": "demo123"})
        if response.status_code == 200:
            token = response.json().get("data", {}).get("access_token")
            print(f"Login successful, token: {token[:20]}...")
            headers = {"Authorization": f"Bearer {token}"}
            
            # Test key endpoints
            tests = [
                ("/api/v1/auth/me", "GET"),
                ("/api/v1/knowledge/points", "GET"),
                ("/api/v1/knowledge/graph", "GET"),
                ("/api/v1/homework", "GET"),
                ("/api/v1/portrait/demo", "GET"),
                ("/api/v1/intelligence/chat/message", "POST", {"student_id": "s1", "message": "hello"}),
            ]
            
            print("\n=== Testing Key Endpoints ===")
            for test in tests:
                path = test[0]
                method = test[1]
                data = test[2] if len(test) > 2 else None
                
                try:
                    if method == "GET":
                        response = await client.get(path, headers=headers)
                    else:
                        response = await client.post(path, headers=headers, json=data)
                    print(f"{method} {path}: {response.status_code}")
                except Exception as e:
                    print(f"{method} {path}: ERROR - {str(e)[:50]}")
        else:
            print(f"Login failed: {response.status_code}")
    
    # Check frontend
    print("\n=== Testing Frontend ===")
    async with httpx.AsyncClient(base_url=frontend_url, timeout=10.0) as client:
        try:
            response = await client.get("/")
            print(f"Frontend /: {response.status_code}")
            if response.status_code == 200:
                # Check for key elements
                content = response.text
                if "AI-Agent" in content or "教育平台" in content:
                    print("Frontend contains expected content!")
        except Exception as e:
            print(f"Frontend check failed: {e}")
    
    print("\n=== Summary ===")
    print("Backend is running at http://localhost:8000")
    print("API docs available at http://localhost:8000/docs")
    print("Frontend should be configured to proxy /api to backend")

if __name__ == "__main__":
    asyncio.run(test_integration())
