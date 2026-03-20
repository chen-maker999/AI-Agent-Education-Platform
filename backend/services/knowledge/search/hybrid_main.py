"""统一检索引擎 - 整合 TF-IDF 语义检索 + BM25 关键词检索"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio

router = APIRouter(prefix="/search/hybrid", tags=["Hybrid Search"])

# 检索结果缓存
search_cache: Dict[str, Dict] = {}


class HybridSearchRequest(BaseModel):
    """混合检索请求"""
    query: str
    course_id: Optional[str] = None
    top_k: int = 10
    semantic_weight: float = 0.5  # 语义检索权重
    keyword_weight: float = 0.5   # 关键词检索权重
    use_cache: bool = True


class HybridSearchResponse(BaseModel):
    """混合检索响应"""
    query: str
    semantic_results: List[Dict]
    keyword_results: List[Dict]
    fused_results: List[Dict]
    total_results: int
    processing_time: float


async def semantic_search_tfidf(query: str, top_k: int = 10) -> List[Dict]:
    """TF-IDF 语义检索"""
    try:
        from services.knowledge.embedding.tfidf_main import search_tfidf
        results = await search_tfidf(query, top_k)
        return results
    except Exception as e:
        print(f"TF-IDF检索失败: {e}")
        return []


async def keyword_search_bm25(query: str, top_k: int = 10) -> List[Dict]:
    """BM25 关键词检索"""
    try:
        from services.knowledge.search.bm25_main import search_bm25
        results = await search_bm25(query, top_k)
        return results
    except Exception as e:
        print(f"BM25检索失败: {e}")
        return []


def fuse_results(
    semantic_results: List[Dict],
    keyword_results: List[Dict],
    semantic_weight: float = 0.5,
    keyword_weight: float = 0.5,
    top_k: int = 10
) -> List[Dict]:
    """融合语义检索和关键词检索结果"""
    
    # 创建doc_id到分数的映射
    doc_scores: Dict[str, Dict] = {}
    
    # 处理语义检索结果
    for result in semantic_results:
        doc_id = result.get('doc_id')
        score = result.get('score', 0) * semantic_weight
        if doc_id not in doc_scores:
            doc_scores[doc_id] = {
                'doc_id': doc_id,
                'content': result.get('content', ''),
                'semantic_score': result.get('score', 0),
                'keyword_score': 0,
                'fused_score': score
            }
        else:
            doc_scores[doc_id]['semantic_score'] = result.get('score', 0)
            doc_scores[doc_id]['fused_score'] += score
    
    # 处理关键词检索结果
    for result in keyword_results:
        doc_id = result.get('doc_id')
        score = result.get('score', 0) * keyword_weight
        if doc_id not in doc_scores:
            doc_scores[doc_id] = {
                'doc_id': doc_id,
                'content': result.get('content', ''),
                'semantic_score': 0,
                'keyword_score': result.get('score', 0),
                'fused_score': score
            }
        else:
            doc_scores[doc_id]['keyword_score'] = result.get('score', 0)
            doc_scores[doc_id]['fused_score'] += score
    
    # 归一化分数
    if doc_scores:
        max_semantic = max((v['semantic_score'] for v in doc_scores.values()), default=1)
        max_keyword = max((v['keyword_score'] for v in doc_scores.values()), default=1)
        
        for doc_id, data in doc_scores.items():
            data['semantic_score'] = data['semantic_score'] / max_semantic if max_semantic > 0 else 0
            data['keyword_score'] = data['keyword_score'] / max_keyword if max_keyword > 0 else 0
            data['fused_score'] = data['semantic_score'] * semantic_weight + data['keyword_score'] * keyword_weight
    
    # 排序
    sorted_results = sorted(doc_scores.values(), key=lambda x: x['fused_score'], reverse=True)
    
    # 添加排名
    results = []
    for i, item in enumerate(sorted_results[:top_k]):
        results.append({
            'doc_id': item['doc_id'],
            'content': item['content'],
            'score': item['fused_score'],
            'semantic_score': item['semantic_score'],
            'keyword_score': item['keyword_score'],
            'rank': i + 1
        })
    
    return results


@router.post("/", response_model=HybridSearchResponse)
async def hybrid_search(request: HybridSearchRequest):
    """混合检索接口 - 语义+关键词"""
    start_time = datetime.now()
    
    # 检查缓存
    cache_key = f"{request.query}:{request.course_id}:{request.semantic_weight}:{request.keyword_weight}"
    if request.use_cache and cache_key in search_cache:
        cached = search_cache[cache_key]
        if (datetime.utcnow() - cached["timestamp"]).seconds < 300:
            return cached["result"]
    
    # 并发执行两种检索
    semantic_task = semantic_search_tfidf(request.query, request.top_k)
    keyword_task = keyword_search_bm25(request.query, request.top_k)
    
    semantic_results, keyword_results = await asyncio.gather(semantic_task, keyword_task)
    
    # 融合结果
    fused_results = fuse_results(
        semantic_results,
        keyword_results,
        request.semantic_weight,
        request.keyword_weight,
        request.top_k
    )
    
    processing_time = (datetime.now() - start_time).total_seconds()
    
    response = HybridSearchResponse(
        query=request.query,
        semantic_results=semantic_results,
        keyword_results=keyword_results,
        fused_results=fused_results,
        total_results=len(fused_results),
        processing_time=processing_time
    )
    
    # 缓存结果
    search_cache[cache_key] = {
        "result": response,
        "timestamp": datetime.utcnow()
    }
    
    return response


@router.post("/semantic")
async def search_semantic_only(query: str, top_k: int = 10):
    """仅语义检索"""
    results = await semantic_search_tfidf(query, top_k)
    return {
        "code": 200,
        "message": "success",
        "data": {"results": results, "total": len(results)}
    }


@router.post("/keyword")
async def search_keyword_only(query: str, top_k: int = 10):
    """仅关键词检索"""
    results = await keyword_search_bm25(query, top_k)
    return {
        "code": 200,
        "message": "success",
        "data": {"results": results, "total": len(results)}
    }


@router.get("/cache/stats")
async def get_cache_stats():
    """获取缓存统计"""
    return {
        "code": 200,
        "data": {"cache_size": len(search_cache)}
    }


@router.post("/cache/clear")
async def clear_cache():
    """清空缓存"""
    global search_cache
    search_cache.clear()
    return {"code": 200, "message": "缓存已清空"}
