"""检查数据库中的文档course_id"""
import requests

BASE_URL = "http://localhost:8000/api/v1"

# 查看所有文档
response = requests.get(f"{BASE_URL}/knowledge/rag/documents", params={"course_id": "default"})
print(f"default 文档: {response.json()}")

response = requests.get(f"{BASE_URL}/knowledge/rag/documents", params={"course_id": "kb_d7e5008075b9"})
print(f"kb_d7e5008075b9 文档: {response.json()}")
