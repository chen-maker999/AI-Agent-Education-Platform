"""Test streaming chat endpoint"""
import requests
import json

def test_stream():
    url = "http://localhost:8000/api/v1/chat/message/stream"
    data = {
        "message": "请用一句话介绍Python",
        "student_id": "test",
        "session_id": "test_stream",
        "mode": "general"
    }

    print("Testing streaming chat endpoint...")
    print(f"URL: {url}")
    print()

    try:
        response = requests.post(url, json=data, stream=True, timeout=60)
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type')}")
        print()

        full_text = ""
        for line in response.iter_lines():
            if line:
                decoded = line.decode('utf-8')
                if decoded.startswith("data: "):
                    data_str = decoded[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        parsed = json.loads(data_str)
                        if "content" in parsed:
                            content = parsed["content"]
                            full_text += content
                            print(content, end="", flush=True)
                        elif "done" in parsed:
                            print()
                            print(f"\n[DONE] Session: {parsed.get('session_id')}")
                    except json.JSONDecodeError:
                        pass

        print(f"\n\nFull response: {full_text}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_stream()
