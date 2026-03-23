"""Test the actual API endpoint with verbose error output"""
import requests
import traceback

url = "http://localhost:8000/api/v1/knowledge/rag/chat"
data = {
    "query": "hello",
    "student_id": "test"
}

print("Testing API with verbose error output...")

try:
    response = requests.post(url, json=data, timeout=60)
    print(f"Status: {response.status_code}")
    print(f"Headers: {response.headers}")
    print(f"Content: {response.text}")
except Exception as e:
    print(f"Request error: {e}")
    traceback.print_exc()
