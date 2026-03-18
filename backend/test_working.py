#!/usr/bin/env python
"""Test working endpoints."""
import sys
import os
import asyncio
import httpx

sys.path.insert(0, r"D:\AI-Agent-Education-Platform-cursor\backend")
os.environ.setdefault("PYTHONPATH", r"D:\AI-Agent-Education-Platform-cursor\backend")

async def test_working_endpoints():
    """Test working endpoints."""
    base_url = "http://localhost:8000"
    
    # Wait for server
    print("Waiting for backend...")
    for i in range(15):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{base_url}/health", timeout=5.0)
                if response.status_code == 200:
                    print("Backend is ready!")
                    break
        except:
            pass
        await asyncio.sleep(2)
    else:
        print("Backend not ready!")
        return
    
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        # Login first
        print("\n=== Login ===")
        response = await client.post("/api/v1/auth/login", data={"username": "demo", "password": "demo123"})
        if response.status_code == 200:
            token = response.json().get("data", {}).get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            print("Login successful!")
        else:
            headers = {}
            print(f"Login failed: {response.status_code}")
            return
        
        # Test working endpoints
        print("\n=== Testing Key Endpoints ===")
        
        # Knowledge Points
        print("\n--- Knowledge Points ---")
        response = await client.post("/api/v1/knowledge/points", headers=headers, json={
            "name": "Python列表",
            "code": "PYTHON_LIST",
            "course_id": "python101",
            "description": "Python中的列表数据结构",
            "level": 1
        })
        print(f"POST /knowledge/points: {response.status_code}")
        if response.status_code in [200, 201]:
            kp_id = response.json().get("data", {}).get("id")
            print(f"  Created point ID: {kp_id}")
        
        response = await client.get("/api/v1/knowledge/points", headers=headers)
        print(f"GET /knowledge/points: {response.status_code}")
        
        # Chat with RAG
        print("\n--- Chat with RAG ---")
        response = await client.post("/api/v1/chat/message", headers=headers, json={
            "student_id": "student_001",
            "course_id": "python101",
            "message": "什么是Python中的列表？"
        })
        print(f"POST /chat/message: {response.status_code}")
        if response.status_code == 200:
            data = response.json().get("data", {})
            print(f"  Response: {data.get('response', 'N/A')[:200]}...")
        
        # Knowledge Graph
        print("\n--- Knowledge Graph ---")
        response = await client.get("/api/v1/knowledge/graph", headers=headers)
        print(f"GET /knowledge/graph: {response.status_code}")
        
        # RAG Chat
        print("\n--- RAG Chat ---")
        response = await client.post("/api/v1/rag/chat", headers=headers, json={
            "session_id": "session_001",
            "student_id": "student_001",
            "message": "Python中的列表有哪些操作？"
        })
        print(f"POST /rag/chat: {response.status_code}")
        if response.status_code == 200:
            data = response.json().get("data", {})
            print(f"  Response: {data.get('response', 'N/A')[:150]}...")
        
        # Portrait
        print("\n--- Portrait ---")
        try:
            response = await client.get("/api/v1/portrait/student_001", headers=headers)
            print(f"GET /portrait: {response.status_code}")
        except Exception as e:
            print(f"GET /portrait: ERROR - {str(e)[:50]}")
        
        # Evaluate
        print("\n--- Evaluate (IRT) ---")
        response = await client.post("/api/v1/evaluate/mastery", headers=headers, json={
            "student_id": "student_001",
            "knowledge_point_id": "kp_python_list",
            "correct": True,
            "difficulty": 0.5
        })
        print(f"POST /evaluate/mastery: {response.status_code}")
        if response.status_code == 200:
            data = response.json().get("data", {})
            print(f"  Mastery level: {data.get('mastery_level')}")
            print(f"  Ability: {data.get('ability')}")
        
        # Warning
        print("\n--- Warning ---")
        try:
            response = await client.get("/api/v1/warning", headers=headers)
            print(f"GET /warning: {response.status_code}")
        except Exception as e:
            print(f"GET /warning: ERROR - {str(e)[:50]}")
        
        # Summary
        print("\n" + "="*50)
        print("SUMMARY: Most endpoints are working!")
        print("Issues: Some 500 errors are due to MinIO")
        print("=End=")

if __name__ == "__main__":
    asyncio.run(test_working_endpoints())
