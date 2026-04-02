"""Tavily 搜索 API 集成"""
import httpx
from typing import Optional, Dict, Any, List


# 全局默认 API Key（用户提供的）
DEFAULT_TAVILY_API_KEY = "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"

# Tavily API URL
TAVILY_API_URL = "https://api.tavily.com/search"


class TavilyClient:
    """Tavily 搜索 API 客户端"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or DEFAULT_TAVILY_API_KEY
        self.timeout = httpx.Timeout(30.0, connect=10.0)

    async def search(
        self,
        query: str,
        max_results: int = 10,
        include_answer: bool = False,
        include_raw_content: bool = False,
        include_images: bool = False,
        search_depth: str = "basic"  # "basic" or "advanced"
    ) -> Dict[str, Any]:
        """
        执行 Tavily 搜索

        Args:
            query: 搜索查询
            max_results: 最大结果数 (1-20)
            include_answer: 是否包含 AI 生成的答案摘要
            include_raw_content: 是否包含原始内容
            include_images: 是否包含图片
            search_depth: 搜索深度 "basic" 或 "advanced"

        Returns:
            {
                "success": bool,
                "answer": str,  # 如果 include_answer=True
                "results": [
                    {
                        "title": str,
                        "url": str,
                        "content": str,
                        "score": float,
                        "published_date": str
                    }
                ],
                "images": List[str],  # 如果 include_images=True
                "response_time": float
            }
        """
        if not self.api_key:
            return {
                "success": False,
                "error": "Tavily API key not configured"
            }

        payload = {
            "api_key": self.api_key,
            "query": query,
            "max_results": min(max_results, 20),
            "include_answer": include_answer,
            "include_raw_content": include_raw_content,
            "include_images": include_images,
            "search_depth": search_depth
        }

        try:
            print(f"[DEBUG TavilyClient.search] Sending request to {TAVILY_API_URL}", flush=True)
            print(f"[DEBUG TavilyClient.search] Payload: {payload}", flush=True)

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    TAVILY_API_URL,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )

                print(f"[DEBUG TavilyClient.search] Response status: {response.status_code}", flush=True)
                print(f"[DEBUG TavilyClient.search] Response body: {response.text[:500]}", flush=True)

                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "answer": data.get("answer"),
                        "results": data.get("results", []),
                        "images": data.get("images", []),
                        "response_time": data.get("response_time", 0)
                    }
                elif response.status_code == 401:
                    return {
                        "success": False,
                        "error": "Invalid API key"
                    }
                elif response.status_code == 429:
                    return {
                        "success": False,
                        "error": "Rate limit exceeded"
                    }
                else:
                    error_detail = response.text
                    print(f"[ERROR TavilyClient.search] API error {response.status_code}: {error_detail}", flush=True)
                    return {
                        "success": False,
                        "error": f"API error {response.status_code}: {error_detail[:200]}"
                    }

        except httpx.TimeoutException:
            print("[ERROR TavilyClient.search] Request timeout", flush=True)
            return {
                "success": False,
                "error": "Request timeout"
            }
        except httpx.RequestError as e:
            print(f"[ERROR TavilyClient.search] Request error: {e}", flush=True)
            return {
                "success": False,
                "error": f"Request error: {str(e)}"
            }
        except Exception as e:
            import traceback
            print(f"[ERROR TavilyClient.search] Unexpected error: {traceback.format_exc()}", flush=True)
            return {
                "success": False,
                "error": str(e)
            }

    async def search_with_context(
        self,
        query: str,
        max_results: int = 10
    ) -> Dict[str, Any]:
        """
        带上下文的搜索（推荐使用）

        Args:
            query: 搜索查询
            max_results: 最大结果数

        Returns:
            搜索结果，包含答案摘要
        """
        return await self.search(
            query=query,
            max_results=max_results,
            include_answer=True,
            search_depth="basic"  # dev API key 不支持 advanced
        )


# 全局客户端
tavily_client = TavilyClient()


async def tavily_search(
    query: str,
    max_results: int = 10,
    api_key: str = None
) -> Dict[str, Any]:
    """
    Tavily 搜索快捷函数

    Args:
        query: 搜索查询
        max_results: 最大结果数
        api_key: 可选的 API key

    Returns:
        搜索结果
    """
    client = TavilyClient(api_key) if api_key else tavily_client
    return await client.search_with_context(query, max_results)
