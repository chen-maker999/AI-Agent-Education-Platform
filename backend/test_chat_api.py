"""测试对话服务API"""
import requests
import json

# 测试聊天API
url = "http://localhost:8000/api/v1/chat/message"
data = {
    "student_id": "test_user",
    "message": "你好",
    "mode": "general"
}

print("正在测试对话服务...")
print(f"URL: {url}")
print(f"请求数据: {json.dumps(data, ensure_ascii=False)}")

try:
    response = requests.post(url, json=data, timeout=60)
    print(f"\n状态码: {response.status_code}")
    print(f"响应内容: {response.text}")
except requests.exceptions.Timeout:
    print("请求超时！可能是API处理时间过长或Kimi服务无响应")
except requests.exceptions.ConnectionError as e:
    print(f"连接失败: {e}")
except Exception as e:
    print(f"请求失败: {e}")
