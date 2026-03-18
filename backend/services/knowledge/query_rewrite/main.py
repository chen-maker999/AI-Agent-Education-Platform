"""查询改写服务 (QUERY-REWRITE) - 使用Kimi API进行查询扩展"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib
import json
import re

router = APIRouter(prefix="/query", tags=["Query Rewrite"])

# 查询缓存
query_cache: Dict[str, Dict] = {}

# 改写提示词模板
REWRITE_PROMPT_TEMPLATE = """请将以下学生问题扩展为更详细的搜索查询，包含同义词和相关概念。
要求：返回3个扩展查询，每行一个。
原始问题：{query}
课程上下文：{course_context}
返回格式：每行一个扩展查询"""


class QueryRewriteRequest(BaseModel):
    """查询改写请求"""
    query: str
    course_context: Optional[str] = ""
    use_cache: bool = True


class QueryRewriteResponse(BaseModel):
    """查询改写响应"""
    original_query: str
    expanded_queries: List[str]
    processing_time: float


async def rewrite_query(query: str, course_context: str = "") -> List[str]:
    """使用Kimi API进行查询改写"""
    # 检查缓存
    cache_key = hashlib.md5(f"{query}:{course_context}".encode()).hexdigest()
    if cache_key in query_cache:
        cached = query_cache[cache_key]
        if (datetime.utcnow() - cached["timestamp"]).seconds < 3600:
            return cached["expanded_queries"]
    
    # 构建提示词
    prompt = REWRITE_PROMPT_TEMPLATE.format(query=query, course_context=course_context)
    
    try:
        from common.integration.kimi import get_kimi_response
        
        response = await get_kimi_response(
            prompt=prompt,
            system_prompt="你是一个查询优化助手，擅长将用户问题扩展为更适合搜索的查询。",
            temperature=0.3,
            max_tokens=200
        )
        
        # 解析响应
        expanded_queries = []
        for line in response.strip().split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                cleaned = re.sub(r'^\d+[\.\)]\s*', '', line)
                if cleaned:
                    expanded_queries.append(cleaned)
        
        if not expanded_queries:
            expanded_queries = [query]
        
        query_cache[cache_key] = {
            "expanded_queries": expanded_queries,
            "timestamp": datetime.utcnow()
        }
        
        return expanded_queries
        
    except Exception as e:
        return [query, f"{query} 详解", f"{query} 例子"]


@router.post("/rewrite", response_model=QueryRewriteResponse)
async def rewrite_query_endpoint(request: QueryRewriteRequest):
    """查询改写接口"""
    start_time = datetime.now()
    expanded_queries = await rewrite_query(request.query, request.course_context)
    processing_time = (datetime.now() - start_time).total_seconds()
    
    return QueryRewriteResponse(
        original_query=request.query,
        expanded_queries=expanded_queries,
        processing_time=processing_time
    )


@router.get("/cache/stats")
async def get_cache_stats():
    return {"code": 200, "message": "success", "data": {"cache_size": len(query_cache)}}


@router.post("/cache/clear")
async def clear_cache():
    global query_cache
    query_cache.clear()
    return {"code": 200, "message": "缓存已清空"}
