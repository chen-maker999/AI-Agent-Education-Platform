"""
查询改写与翻译服务 (QUERY REWRITE & TRANSLATION)

P11 优化:
1. 添加查询翻译功能 (中文→英文)
2. 支持 HyDE (假设文档嵌入)
3. 支持查询分解 (Query Decomposition)
4. 增强的查询扩展策略
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib
import json
import re
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/query", tags=["Query Understanding"])

# 查询缓存
query_cache: Dict[str, Dict] = {}
translation_cache: Dict[str, str] = {}
hyde_cache: Dict[str, str] = {}

# ==================== 提示词模板 ====================

# 查询翻译提示词 (中文→英文)
TRANSLATE_PROMPT_TEMPLATE = """请将以下中文查询翻译为准确的英文技术术语查询。
要求：
1. 保持专业术语的准确性
2. 使用计算机科学/工程领域的标准英文表达
3. 不要添加解释，只返回翻译结果

中文查询：{query}
课程上下文：{course_context}

英文翻译："""

# 查询扩展提示词
EXPAND_PROMPT_TEMPLATE = """请将以下学生问题扩展为更详细的搜索查询，包含同义词和相关概念。
要求：返回 3 个扩展查询，每行一个。
原始问题：{query}
课程上下文：{course_context}
返回格式：每行一个扩展查询"""

# HyDE (假设文档嵌入) 提示词
HYDE_PROMPT_TEMPLATE = """请为以下问题生成一个假设的答案段落。
要求：
1. 答案应该详细、准确，包含关键技术概念
2. 使用英文回答 (因为文档是英文的)
3. 答案长度约 100-150 词
4. 包含相关的技术术语和解释

问题：{query}
课程上下文：{course_context}

假设答案："""

# 查询分解提示词
DECOMPOSE_PROMPT_TEMPLATE = """请将以下复杂问题分解为 2-4 个简单的子问题。
要求：
1. 每个子问题应该独立且具体
2. 子问题应该覆盖原问题的所有关键方面
3. 使用英文返回子问题

原始问题：{query}
课程上下文：{course_context}

子问题 (每行一个)："""


# ==================== 数据模型 ====================

class QueryTranslateRequest(BaseModel):
    """查询翻译请求"""
    query: str
    course_context: Optional[str] = ""
    use_cache: bool = True


class QueryTranslateResponse(BaseModel):
    """查询翻译响应"""
    original_query: str
    translated_query: str
    processing_time_ms: float


class QueryRewriteRequest(BaseModel):
    """查询改写请求"""
    query: str
    course_context: Optional[str] = ""
    use_cache: bool = True


class QueryRewriteResponse(BaseModel):
    """查询改写响应"""
    original_query: str
    expanded_queries: List[str]
    processing_time_ms: float


class HyDERequest(BaseModel):
    """HyDE 请求"""
    query: str
    course_context: Optional[str] = ""
    use_cache: bool = True


class HyDEResponse(BaseModel):
    """HyDE 响应"""
    query: str
    hypothetical_answer: str
    processing_time_ms: float


class QueryDecomposeRequest(BaseModel):
    """查询分解请求"""
    query: str
    course_context: Optional[str] = ""
    use_cache: bool = True


class QueryDecomposeResponse(BaseModel):
    """查询分解响应"""
    original_query: str
    sub_queries: List[str]
    processing_time_ms: float


class QueryUnderstandingRequest(BaseModel):
    """综合查询理解请求"""
    query: str
    course_context: Optional[str] = ""
    enable_translation: bool = True
    enable_expansion: bool = False
    enable_hyde: bool = False
    enable_decomposition: bool = False


class QueryUnderstandingResponse(BaseModel):
    """综合查询理解响应"""
    original_query: str
    translated_query: Optional[str] = None
    expanded_queries: Optional[List[str]] = None
    hypothetical_answer: Optional[str] = None
    sub_queries: Optional[List[str]] = None
    processing_time_ms: float


# ==================== 核心功能 ====================

async def translate_query(query: str, course_context: str = "", use_cache: bool = True) -> str:
    """
    将中文查询翻译为英文
    
    跨语言检索的关键步骤：将中文查询翻译为英文，然后检索英文文档
    """
    # 检查缓存
    cache_key = f"{query}:{course_context}"
    if use_cache and cache_key in translation_cache:
        logger.debug(f"翻译缓存命中：{query[:20]}...")
        return translation_cache[cache_key]
    
    # 构建提示词
    prompt = TRANSLATE_PROMPT_TEMPLATE.format(query=query, course_context=course_context)
    
    try:
        from common.integration.kimi import get_kimi_response
        
        response = await get_kimi_response(
            prompt=prompt,
            system_prompt="你是一个专业的技术翻译，擅长将中文技术问题翻译为准确的英文。",
            temperature=0.1,
            max_tokens=100
        )
        
        # 清理响应
        translated = response.strip()
        
        # 如果翻译失败或返回空，返回原查询
        if not translated:
            translated = query
        
        # 缓存翻译结果
        if use_cache:
            translation_cache[cache_key] = translated
        
        logger.info(f"查询翻译完成：{query[:30]}... → {translated[:30]}...")
        return translated
        
    except Exception as e:
        logger.error(f"查询翻译失败：{e}，返回原查询")
        return query


async def rewrite_query(query: str, course_context: str = "", use_cache: bool = True) -> List[str]:
    """使用 Kimi API 进行查询改写"""
    # 检查缓存
    cache_key = hashlib.md5(f"{query}:{course_context}".encode()).hexdigest()
    if use_cache and cache_key in query_cache:
        cached = query_cache[cache_key]
        if (datetime.utcnow() - cached["timestamp"]).seconds < 3600:
            return cached["expanded_queries"]
    
    # 构建提示词
    prompt = EXPAND_PROMPT_TEMPLATE.format(query=query, course_context=course_context)
    
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
        
        if use_cache:
            query_cache[cache_key] = {
                "expanded_queries": expanded_queries,
                "timestamp": datetime.utcnow()
            }
        
        return expanded_queries
        
    except Exception as e:
        logger.error(f"查询改写失败：{e}")
        return [query, f"{query} 详解", f"{query} 例子"]


async def generate_hyde_answer(query: str, course_context: str = "", use_cache: bool = True) -> str:
    """
    生成假设答案 (HyDE: Hypothetical Document Embedding)
    
    HyDE 原理：生成一个假设的答案，然后用假设答案的嵌入进行检索
    这样可以找到与答案语义更相似的文档
    """
    # 检查缓存
    cache_key = f"{query}:{course_context}"
    if use_cache and cache_key in hyde_cache:
        logger.debug(f"HyDE 缓存命中：{query[:20]}...")
        return hyde_cache[cache_key]
    
    # 构建提示词
    prompt = HYDE_PROMPT_TEMPLATE.format(query=query, course_context=course_context)
    
    try:
        from common.integration.kimi import get_kimi_response
        
        response = await get_kimi_response(
            prompt=prompt,
            system_prompt="你是一个 AI 助手，擅长生成准确、详细的技术答案。请用英文回答。",
            temperature=0.5,
            max_tokens=200
        )
        
        hypothetical = response.strip()
        
        if not hypothetical:
            hypothetical = query
        
        if use_cache:
            hyde_cache[cache_key] = hypothetical
        
        logger.info(f"HyDE 答案生成完成：{query[:30]}...")
        return hypothetical
        
    except Exception as e:
        logger.error(f"HyDE 答案生成失败：{e}")
        return query


async def decompose_query(query: str, course_context: str = "", use_cache: bool = True) -> List[str]:
    """
    查询分解 (Query Decomposition)
    
    将复杂问题分解为多个简单的子问题，分别检索后再综合
    """
    cache_key = f"decompose:{query}:{course_context}"
    
    # 检查缓存
    if use_cache and cache_key in query_cache:
        cached = query_cache[cache_key]
        if (datetime.utcnow() - cached["timestamp"]).seconds < 3600:
            return cached["sub_queries"]
    
    # 构建提示词
    prompt = DECOMPOSE_PROMPT_TEMPLATE.format(query=query, course_context=course_context)
    
    try:
        from common.integration.kimi import get_kimi_response
        
        response = await get_kimi_response(
            prompt=prompt,
            system_prompt="你是一个问题分析专家，擅长将复杂问题分解为简单的子问题。请用英文返回。",
            temperature=0.3,
            max_tokens=250
        )
        
        # 解析响应
        sub_queries = []
        for line in response.strip().split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                cleaned = re.sub(r'^\d+[\.\)]\s*', '', line)
                if cleaned:
                    sub_queries.append(cleaned)
        
        if not sub_queries:
            sub_queries = [query]
        
        if use_cache:
            query_cache[cache_key] = {
                "sub_queries": sub_queries,
                "timestamp": datetime.utcnow()
            }
        
        logger.info(f"查询分解完成：{query[:30]}... → {len(sub_queries)} 个子问题")
        return sub_queries
        
    except Exception as e:
        logger.error(f"查询分解失败：{e}")
        return [query]


async def understand_query(
    query: str,
    course_context: str = "",
    enable_translation: bool = True,
    enable_expansion: bool = False,
    enable_hyde: bool = False,
    enable_decomposition: bool = False,
    use_cache: bool = True
) -> Dict[str, Any]:
    """
    综合查询理解
    
    根据配置启用不同的查询理解策略
    """
    start_time = datetime.now()
    result = {
        "original_query": query
    }
    
    # 查询翻译 (跨语言检索关键步骤)
    if enable_translation:
        translated = await translate_query(query, course_context, use_cache)
        result["translated_query"] = translated
    
    # 查询扩展
    if enable_expansion:
        expanded = await rewrite_query(query, course_context, use_cache)
        result["expanded_queries"] = expanded
    
    # HyDE
    if enable_hyde:
        hyde_answer = await generate_hyde_answer(query, course_context, use_cache)
        result["hypothetical_answer"] = hyde_answer
    
    # 查询分解
    if enable_decomposition:
        sub_queries = await decompose_query(query, course_context, use_cache)
        result["sub_queries"] = sub_queries
    
    result["processing_time_ms"] = (datetime.now() - start_time).total_seconds() * 1000
    
    return result


# ==================== API 端点 ====================

@router.post("/translate", response_model=QueryTranslateResponse)
async def translate_query_endpoint(request: QueryTranslateRequest):
    """
    查询翻译接口 (中文→英文)
    
    跨语言检索的关键步骤：将中文查询翻译为英文，然后检索英文文档
    """
    start_time = datetime.now()
    
    translated = await translate_query(
        query=request.query,
        course_context=request.course_context,
        use_cache=request.use_cache
    )
    
    processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000
    
    return QueryTranslateResponse(
        original_query=request.query,
        translated_query=translated,
        processing_time_ms=processing_time_ms
    )


@router.post("/rewrite", response_model=QueryRewriteResponse)
async def rewrite_query_endpoint(request: QueryRewriteRequest):
    """查询改写接口"""
    start_time = datetime.now()
    expanded_queries = await rewrite_query(
        query=request.query,
        course_context=request.course_context,
        use_cache=request.use_cache
    )
    processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000
    
    return QueryRewriteResponse(
        original_query=request.query,
        expanded_queries=expanded_queries,
        processing_time_ms=processing_time_ms
    )


@router.post("/hyde", response_model=HyDEResponse)
async def hyde_endpoint(request: HyDERequest):
    """
    HyDE (假设文档嵌入) 接口
    
    生成假设答案，然后用假设答案的嵌入进行检索
    """
    start_time = datetime.now()
    hypothetical = await generate_hyde_answer(
        query=request.query,
        course_context=request.course_context,
        use_cache=request.use_cache
    )
    processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000
    
    return HyDEResponse(
        query=request.query,
        hypothetical_answer=hypothetical,
        processing_time_ms=processing_time_ms
    )


@router.post("/decompose", response_model=QueryDecomposeResponse)
async def decompose_query_endpoint(request: QueryDecomposeRequest):
    """
    查询分解接口
    
    将复杂问题分解为多个简单的子问题
    """
    start_time = datetime.now()
    sub_queries = await decompose_query(
        query=request.query,
        course_context=request.course_context,
        use_cache=request.use_cache
    )
    processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000
    
    return QueryDecomposeResponse(
        original_query=request.query,
        sub_queries=sub_queries,
        processing_time_ms=processing_time_ms
    )


@router.post("/understand", response_model=QueryUnderstandingResponse)
async def understand_query_endpoint(request: QueryUnderstandingRequest):
    """
    综合查询理解接口
    
    可配置启用不同的查询理解策略
    """
    start_time = datetime.now()
    
    result = await understand_query(
        query=request.query,
        course_context=request.course_context,
        enable_translation=request.enable_translation,
        enable_expansion=request.enable_expansion,
        enable_hyde=request.enable_hyde,
        enable_decomposition=request.enable_decomposition,
        use_cache=request.use_cache
    )
    
    processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000
    
    return QueryUnderstandingResponse(
        original_query=request.query,
        translated_query=result.get("translated_query"),
        expanded_queries=result.get("expanded_queries"),
        hypothetical_answer=result.get("hypothetical_answer"),
        sub_queries=result.get("sub_queries"),
        processing_time_ms=processing_time_ms
    )


@router.get("/cache/stats")
async def get_cache_stats():
    """获取缓存统计"""
    return {
        "code": 200,
        "data": {
            "translation_cache_size": len(translation_cache),
            "rewrite_cache_size": len(query_cache),
            "hyde_cache_size": len(hyde_cache)
        }
    }


@router.post("/cache/clear")
async def clear_cache():
    """清空所有缓存"""
    global query_cache, translation_cache, hyde_cache
    query_cache.clear()
    translation_cache.clear()
    hyde_cache.clear()
    return {"code": 200, "message": "所有缓存已清空"}


# ==================== 便捷函数 ====================

async def translate_query_for_retrieval(query: str, course_context: str = "") -> str:
    """
    便捷函数：为检索翻译查询
    
    用于 retriever 中直接调用
    """
    return await translate_query(query, course_context, use_cache=True)
