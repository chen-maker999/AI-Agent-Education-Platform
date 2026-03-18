"""多路检索执行器 - 语义/关键词/图谱检索"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio

router = APIRouter(prefix="/search", tags=["Multi-Channel Search"])

# 检索结果缓存
search_cache: Dict[str, Dict] = {}


class SearchRequest(BaseModel):
    query: str
    course_id: Optional[str] = None
    channels: List[str] = ["semantic", "keyword", "graph"]
    top_k: int = 10
    use_cache: bool = True


class SearchResponse(BaseModel):
    query: str
    channel_results: Dict[str, List[Dict]]
    total_results: int
    processing_time: float


async def semantic_search(query: str, top_k: int = 10) -> List[Dict]:
    """语义搜索 - FAISS向量检索"""
    try:
        from services.knowledge.faiss_indexer.main import search_vectors
        from services.knowledge.embedding.main import generate_embeddings
        
        # 生成查询向量
        embeddings = await generate_embeddings([query])
        import numpy as np
        query_vec = np.array(embeddings[0]).astype('float32')
        
        # 搜索
        results = await search_vectors(query_vec, top_k=top_k)
        
        return results
    except Exception as e:
        return []


async def keyword_search(query: str, course_id: str = None, top_k: int = 10) -> List[Dict]:
    """关键词搜索 - Elasticsearch"""
    try:
        from services.knowledge.es_indexer.main import ESSearchRequest, search_documents
        
        request = ESSearchRequest(
            query=query,
            course_id=course_id,
            top_k=top_k
        )
        results = await search_documents(request)
        return results
    except Exception as e:
        return []


async def graph_search(query: str, course_id: str = None, top_k: int = 10) -> List[Dict]:
    """图谱搜索 - Neo4j"""
    try:
        from services.knowledge.graph.main import query_graph
        
        # 提取关键词进行图查询
        request = {
            "node_type": "KnowledgePoint",
            "depth": 2,
            "limit": top_k
        }
        
        result = await query_graph(request)
        data = result.get("data", {})
        nodes = data.get("nodes", [])
        
        results = []
        for node in nodes:
            results.append({
                "doc_id": node.get("node_id"),
                "content": node.get("name", ""),
                "score": 0.8,
                "node_type": node.get("node_type"),
                "metadata": node.get("properties", {})
            })
        
        return results
    except Exception as e:
        return []


async def multi_channel_search(
    query: str,
    channels: List[str],
    course_id: str = None,
    top_k: int = 10
) -> Dict[str, List[Dict]]:
    """多路并发检索"""
    tasks = {}
    
    if "semantic" in channels:
        tasks["semantic"] = semantic_search(query, top_k)
    
    if "keyword" in channels:
        tasks["keyword"] = keyword_search(query, course_id, top_k)
    
    if "graph" in channels:
        tasks["graph"] = graph_search(query, course_id, top_k)
    
    # 并发执行所有检索任务
    if tasks:
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        
        channel_results = {}
        for channel, result in zip(tasks.keys(), results):
            if isinstance(result, Exception):
                channel_results[channel] = []
            else:
                channel_results[channel] = result
    else:
        channel_results = {}
    
    return channel_results


@router.post("/multi", response_model=SearchResponse)
async def search_multi_channel(request: SearchRequest):
    """多路检索接口"""
    start_time = datetime.now()
    
    # 检查缓存
    cache_key = f"{request.query}:{request.course_id}:{':'.join(request.channels)}"
    if request.use_cache and cache_key in search_cache:
        cached = search_cache[cache_key]
        if (datetime.utcnow() - cached["timestamp"]).seconds < 300:
            return cached["result"]
    
    # 执行多路检索
    channel_results = await multi_channel_search(
        query=request.query,
        channels=request.channels,
        course_id=request.course_id,
        top_k=request.top_k
    )
    
    # 统计总结果数
    total_results = sum(len(results) for results in channel_results.values())
    
    processing_time = (datetime.now() - start_time).total_seconds()
    
    response = SearchResponse(
        query=request.query,
        channel_results=channel_results,
        total_results=total_results,
        processing_time=processing_time
    )
    
    # 缓存结果
    search_cache[cache_key] = {
        "result": response,
        "timestamp": datetime.utcnow()
    }
    
    return response


@router.get("/cache/stats")
async def get_cache_stats():
    return {"code": 200, "data": {"cache_size": len(search_cache)}}


@router.post("/cache/clear")
async def clear_cache():
    global search_cache
    search_cache.clear()
    return {"code": 200, "message": "缓存已清空"}
