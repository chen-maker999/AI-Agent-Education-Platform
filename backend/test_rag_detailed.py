"""Detailed test for RAG chat API"""
import traceback
import requests

def test_rag_chat():
    url = "http://localhost:8000/api/v1/knowledge/rag/chat"
    data = {
        "query": "hello",
        "student_id": "test",
        "use_rewrite": False,  # Disable rewrite to isolate issue
        "use_rerank": False
    }
    
    print("Testing RAG Chat API with use_rewrite=False...")
    try:
        r = requests.post(url, json=data, timeout=60)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text}")
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()

def test_kimi_direct():
    """Test Kimi API directly"""
    from common.integration.kimi import get_kimi_response
    import asyncio
    
    async def test():
        print("\nTesting Kimi API directly...")
        try:
            result = await get_kimi_response(
                prompt="Say hello in one sentence",
                system_prompt="You are a helpful assistant."
            )
            print(f"Kimi response: {result}")
        except Exception as e:
            print(f"Kimi error: {e}")
            traceback.print_exc()
    
    asyncio.run(test())

if __name__ == "__main__":
    import sys
    sys.path.insert(0, '.')
    test_rag_chat()
    test_kimi_direct()
