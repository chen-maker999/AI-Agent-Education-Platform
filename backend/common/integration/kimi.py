"""Kimi API client for LLM interactions."""

import json
from typing import Optional, List, Dict, Any
from common.core.config import settings
import httpx


class KimiClient:
    """Kimi API client."""

    def __init__(self, api_key: str = None, endpoint: str = None, model: str = None):
        self.api_key = api_key or settings.KIMI_API_KEY
        self.endpoint = endpoint or settings.KIMI_API_ENDPOINT
        self.model = model or settings.KIMI_MODEL
        self.timeout = settings.KIMI_TIMEOUT

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> Dict[str, Any]:
        """Send chat completion request to Kimi API."""
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

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=headers)
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": f"API error: {response.status_code}", "detail": response.text}
        except httpx.RequestError as e:
            return {"error": f"Connection error: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}

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


# Singleton instance
kimi_client = KimiClient()


async def get_kimi_response(
    prompt: str,
    system_prompt: str = "You are a helpful teaching assistant.",
    **kwargs
) -> str:
    """Get response from Kimi API."""
    return await kimi_client.chat_completion(prompt, system_prompt, **kwargs)
