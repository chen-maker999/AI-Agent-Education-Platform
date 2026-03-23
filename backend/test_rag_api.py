import requests

# Test RAG chat API
url = "http://localhost:8000/api/v1/knowledge/rag/chat"
data = {
    "query": "hello",
    "student_id": "test"
}

print("Testing RAG Chat API...")
try:
    r = requests.post(url, json=data, timeout=30)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text[:800]}")
except Exception as e:
    print(f"Error: {e}")
