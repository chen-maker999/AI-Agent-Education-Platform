"""Test both chat endpoints"""
import requests
import sys
sys.path.insert(0, '.')

def test_endpoint(url, name):
    print(f"\n{'='*50}")
    print(f"Testing: {name}")
    print(f"URL: {url}")
    print('='*50)
    
    data = {
        "student_id": "test",
        "message": "你好"
    }
    
    try:
        r = requests.post(url, json=data, timeout=60)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            try:
                resp = r.json()
                print(f"Response code: {resp.get('code')}")
                if resp.get('data'):
                    print(f"Response preview: {str(resp.get('data', {}).get('response', resp.get('data', {}).get('answer', '')))[:200]}")
            except:
                print(f"Raw response: {r.text[:500]}")
        else:
            print(f"Error: {r.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    base = "http://localhost:8000/api/v1"
    
    # Test RAG chat (used by frontend)
    test_endpoint(f"{base}/knowledge/rag/chat", "RAG Chat (当前前端使用)")
    
    # Test direct chat
    test_endpoint(f"{base}/chat/message", "Direct Chat Message")
