"""Test RAG endpoint within FastAPI context"""
import asyncio
import sys
sys.path.insert(0, '.')

async def test_api():
    from fastapi.testclient import TestClient
    from main import app
    
    client = TestClient(app)
    
    # Test the endpoint
    response = client.post(
        "/api/v1/knowledge/rag/chat",
        json={
            "query": "hello",
            "student_id": "test"
        }
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")

if __name__ == "__main__":
    asyncio.run(test_api())
