"""Test the fixed chat API call format"""
import requests

def test_fixed_format():
    # This is what the frontend now sends
    url = "http://localhost:8000/api/v1/chat/message"
    data = {
        "message": "你好",
        "student_id": "test",
        "session_id": "chat_general",
        "mode": "general",
        "context": {},
        "tools": None
    }
    
    print("Testing fixed frontend API call format...")
    print(f"URL: {url}")
    print(f"Data: {data}")
    print()
    
    try:
        r = requests.post(url, json=data, timeout=60)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            resp = r.json()
            print(f"Response code: {resp.get('code')}")
            if resp.get('data'):
                answer = resp.get('data', {}).get('response', '')
                print(f"Answer preview: {answer[:200]}...")
            print("\n✅ 修复成功！API调用正常")
        else:
            print(f"❌ Error: {r.text}")
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_fixed_format()
