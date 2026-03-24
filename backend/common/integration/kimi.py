"""Kimi API client for LLM interactions."""

import json
import asyncio
from typing import Optional, List, Dict, Any, AsyncGenerator
from common.core.config import settings
import httpx


class KimiClient:
    """Kimi API client."""

    def __init__(self, api_key: str = None, endpoint: str = None, model: str = None):
        self.api_key = api_key or settings.KIMI_API_KEY
        self.endpoint = endpoint or settings.KIMI_API_ENDPOINT
        self.model = model or settings.KIMI_MODEL
        self.timeout = httpx.Timeout(settings.KIMI_TIMEOUT * 2.0, connect=10.0)  # 增加超时时间
        self.max_retries = 5  # 增加重试次数
        self.retry_delay = 1.0  # 初始重试延迟（秒）

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Send chat completion request to Kimi API with retry logic for rate limits."""
        if not self.api_key:
            return {"error": "Kimi API key not configured", "choices": [{"message": {"content": "API key not configured"}}]}

        url = f"{self.endpoint}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        # 如果有工具定义，添加 tools 参数
        if tools:
            payload["tools"] = tools

        last_error = None
        retry_delay = self.retry_delay

        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(url, json=payload, headers=headers)

                    if response.status_code == 200:
                        return response.json()
                    elif response.status_code == 429:
                        # Rate limit - 重试
                        last_error = f"API rate limit exceeded (429)"
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(retry_delay)
                            retry_delay *= 2  # 指数退避
                            continue
                        else:
                            return {"error": f"API error: {response.status_code} - Rate limit exceeded after {self.max_retries} retries", "detail": response.text}
                    else:
                        return {"error": f"API error: {response.status_code}", "detail": response.text}

            except httpx.RequestError as e:
                last_error = f"Connection error: {str(e)}"
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                    continue
            except asyncio.TimeoutError as e:
                last_error = f"Request timeout: API response exceeded {self.timeout} seconds"
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                    continue
            except Exception as e:
                last_error = f"Unexpected error: {str(e)}"
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                    continue

        # 记录详细错误日志
        import logging
        logging.warning(f"Kimi API调用失败: {last_error}, 尝试次数: {self.max_retries}")
        return {"error": last_error or "Unknown error"}

    async def chat_completion(
        self,
        prompt: str,
        system_prompt: str = "You are a helpful teaching assistant.",
        **kwargs
    ) -> str:
        """Simple chat completion with single prompt."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        result = await self.chat(messages, **kwargs)
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        return result.get("error", "Unknown error")

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Send chat completion request with streaming response."""
        if not self.api_key:
            yield "API key not configured"
            return

        url = f"{self.endpoint}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True  # 启用流式输出
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream("POST", url, json=payload, headers=headers) as response:
                    if response.status_code == 200:
                        async for line in response.aiter_lines():
                            if line.startswith("data: "):
                                data = line[6:]  # 去掉 "data: " 前缀
                                if data.strip() == "[DONE]":
                                    break
                                try:
                                    chunk_data = json.loads(data)
                                    choices = chunk_data.get("choices", [])
                                    if choices:
                                        delta = choices[0].get("delta", {})
                                        content = delta.get("content", "")
                                        if content:
                                            yield content
                                except json.JSONDecodeError:
                                    continue
                    else:
                        error_text = await response.aread()
                        yield f"Error: {response.status_code} - {error_text.decode()}"

        except httpx.RequestError as e:
            yield f"Connection error: {str(e)}"
        except asyncio.TimeoutError:
            yield f"Request timeout"
        except Exception as e:
            yield f"Error: {str(e)}"

    async def chat_stream_simple(
        self,
        prompt: str,
        system_prompt: str = "You are a helpful teaching assistant.",
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Simple streaming chat completion."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        async for chunk in self.chat_stream(messages, **kwargs):
            yield chunk


# Singleton instance
kimi_client = KimiClient()


async def get_kimi_response(
    prompt: str,
    system_prompt: str = "You are a helpful teaching assistant.",
    **kwargs
) -> str:
    """Get response from Kimi API."""
    return await kimi_client.chat_completion(prompt, system_prompt, **kwargs)


async def get_kimi_stream(
    prompt: str,
    system_prompt: str = "You are a helpful teaching assistant.",
    **kwargs
) -> AsyncGenerator[str, None]:
    """Get streaming response from Kimi API."""
    async for chunk in kimi_client.chat_stream_simple(prompt, system_prompt, **kwargs):
        yield chunk
