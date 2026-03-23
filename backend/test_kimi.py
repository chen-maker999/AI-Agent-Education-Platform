"""测试 Kimi API 直接调用"""
import asyncio
import sys
sys.path.insert(0, '.')

from common.integration.kimi import kimi_client
from common.core.config import settings

async def test_kimi():
    print(f"API Endpoint: {settings.KIMI_API_ENDPOINT}")
    print(f"Model: {settings.KIMI_MODEL}")
    print(f"API Key: {settings.KIMI_API_KEY[:10]}..." if settings.KIMI_API_KEY else "No API Key")

    # 测试普通问答（无 tools）
    messages = [
        {"role": "system", "content": "你是一位友好的助手。"},
        {"role": "user", "content": "你好，介绍一下Python的列表。"}
    ]

    print("\n测试普通问答（无 tools）...")
    result = await kimi_client.chat(messages=messages)
    print(f"结果: {result}")

    # 测试带 tools 的调用
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "获取天气信息",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string", "description": "城市名称"}
                    }
                }
            }
        }
    ]

    print("\n测试带 tools 的调用...")
    result2 = await kimi_client.chat(messages=messages, tools=tools)
    print(f"结果: {result2}")

if __name__ == "__main__":
    asyncio.run(test_kimi())
