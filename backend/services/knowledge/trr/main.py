"""
Translate-Retrieve-Rerank (TRR) 完整流程服务

P11 优化:
1. 完整的跨语言检索流程
2. 翻译→检索→重排三阶段
3. 支持多种翻译和重排模型
4. 端到端优化
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pydantic import BaseModel
from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trr", tags=["Translate-Retrieve-Rerank"])


# ==================== 数据模型 ====================

class TRRRequest(BaseModel):
    """TRR 请求"""
    query: str  # 中文查询
    course_id: Optional[str] = None
    top_k: int = 10
    rerank_top_k: int = 5
    enable_translation: bool = True
    enable_hyde: bool = False
    use_cache: bool = True


class TRRResponse(BaseModel):
    """TRR 响应"""
    original_query: str
    translated_query: Optional[str]
    results: List[Dict[str, Any]]
    total_results: int
    stages: Dict[str, Any]
    processing_time_ms: float


class TRRStage(BaseModel):
    """TRR 阶段信息"""
    name: str
    success: bool
    processing_time_ms: float
    details: Dict[str, Any] = {}


# ==================== TRR 核心流程 ====================

async def translate_retrieve_rerank(
    query: str,
    course_id: Optional[str] = None,
    top_k: int = 10,
    rerank_top_k: int = 5,
    enable_translation: bool = True,
    enable_hyde: bool = False,
    use_cache: bool = True
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Translate-Retrieve-Rerank 完整流程
    
    阶段 1: Translate - 将中文查询翻译为英文
    阶段 2: Retrieve - 使用翻译后的查询进行检索
    阶段 3: Rerank - 对检索结果进行重排序
    
    Args:
        query: 中文查询文本
        course_id: 课程 ID
        top_k: 初始检索数量
        rerank_top_k: 重排序后返回数量
        enable_translation: 是否启用翻译
        enable_hyde: 是否启用 HyDE
        use_cache: 是否使用缓存
    
    Returns:
        (重排序后的结果，各阶段统计信息)
    """
    start_time = datetime.now()
    stages = {}
    
    original_query = query

    # ==================== 阶段 1: 翻译 (P11 性能优化) ====================
    stage1_start = datetime.now()
    translated_query = query
    translation_applied = False

    # P11 性能优化：检测查询语言，英文查询跳过翻译
    def is_mostly_english(text: str) -> bool:
        """检测查询是否主要为英文"""
        import re
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        total_chars = len(text.replace(" ", ""))
        return english_chars / max(total_chars, 1) > 0.7

    if enable_translation:
        # P11 优化：英文查询跳过翻译
        if is_mostly_english(query):
            logger.debug(f"TRR 检测到英文查询，跳过翻译：{query[:30]}...")
            translated_query = query
            translation_applied = False
        else:
            try:
                # P11 修复：从正确的模块导入翻译函数
                from services.knowledge.rag.retriever import translate_query_if_needed
                translated_query, translation_applied = await translate_query_if_needed(
                    query,
                    course_context=course_id or ""
                )

                if translation_applied:
                    logger.info(f"TRR 阶段 1 - 翻译：{query[:30]}... → {translated_query[:30]}...")
            except Exception as e:
                logger.error(f"TRR 翻译阶段失败：{e}，使用原查询")
                translated_query = query
    
    stages["translate"] = {
        "name": "Translate",
        "success": True,
        "processing_time_ms": (datetime.now() - stage1_start).total_seconds() * 1000,
        "details": {
            "original_query": original_query,
            "translated_query": translated_query,
            "translation_applied": translation_applied
        }
    }
    
    # ==================== 阶段 2: 检索 ====================
    stage2_start = datetime.now()
    retrieved_results = []
    
    try:
        # 使用 hybrid_search 进行检索
        from services.knowledge.rag.retriever import hybrid_search
        
        retrieved_results, search_stats = await hybrid_search(
            query=translated_query,
            course_id=course_id,
            top_k=top_k,
            use_cache=use_cache,
            enable_translation=False,  # 已经翻译过了
            enable_hyde=enable_hyde,
            request_id=None
        )
        
        logger.info(f"TRR 阶段 2 - 检索：返回 {len(retrieved_results)} 个结果")
        
    except Exception as e:
        logger.error(f"TRR 检索阶段失败：{e}")
    
    stages["retrieve"] = {
        "name": "Retrieve",
        "success": len(retrieved_results) > 0,
        "processing_time_ms": (datetime.now() - stage2_start).total_seconds() * 1000,
        "details": {
            "query_used": translated_query,
            "results_count": len(retrieved_results),
            "stats": search_stats if 'search_stats' in dir() else {}
        }
    }
    
    # ==================== 阶段 3: 重排序 ====================
    stage3_start = datetime.now()
    reranked_results = []
    
    if retrieved_results:
        try:
            from services.knowledge.rerank.main import rerank_documents
            
            reranked_results = await rerank_documents(
                query=translated_query,
                documents=retrieved_results,
                top_k=rerank_top_k
            )
            
            logger.info(f"TRR 阶段 3 - 重排序：返回 {len(reranked_results)} 个结果")
            
        except Exception as e:
            logger.error(f"TRR 重排序阶段失败：{e}，返回原始检索结果")
            reranked_results = retrieved_results[:rerank_top_k]
    
    stages["rerank"] = {
        "name": "Rerank",
        "success": len(reranked_results) > 0,
        "processing_time_ms": (datetime.now() - stage3_start).total_seconds() * 1000,
        "details": {
            "input_count": len(retrieved_results),
            "output_count": len(reranked_results),
            "rerank_top_k": rerank_top_k
        }
    }
    
    # 总体统计
    total_time_ms = (datetime.now() - start_time).total_seconds() * 1000
    
    stats = {
        "total_time_ms": total_time_ms,
        "stages": stages,
        "original_query": original_query,
        "final_query": translated_query,
        "translation_applied": translation_applied
    }
    
    return reranked_results, stats


# ==================== 增强版 TRR (带查询扩展) ====================

async def trr_with_expansion(
    query: str,
    course_id: Optional[str] = None,
    top_k: int = 10,
    rerank_top_k: int = 5,
    expansion_count: int = 3
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    带查询扩展的 TRR 流程
    
    1. 翻译查询
    2. 扩展查询 (同义词、相关概念)
    3. 多查询检索
    4. 结果融合 (RRF)
    5. 重排序
    """
    start_time = datetime.now()
    stages = {}
    
    # 1. 翻译
    from services.knowledge.query_rewrite.main import translate_query
    translated_query = await translate_query(query, course_context=course_id or "")
    
    # 2. 扩展查询
    from services.knowledge.query_rewrite.main import rewrite_query
    expanded_queries = await rewrite_query(translated_query, course_context=course_id or "")
    
    all_queries = [translated_query] + expanded_queries[:expansion_count]
    
    stages["query_expansion"] = {
        "original": query,
        "translated": translated_query,
        "expanded": all_queries
    }
    
    # 3. 多查询检索
    all_results = []
    
    for eq in all_queries:
        try:
            from services.knowledge.rag.retriever import hybrid_search
            results, _ = await hybrid_search(
                query=eq,
                course_id=course_id,
                top_k=top_k,
                enable_translation=False
            )
            all_results.extend(results)
        except Exception as e:
            logger.error(f"扩展查询检索失败：{eq[:20]}... - {e}")
    
    # 4. 结果融合 (RRF - Reciprocal Rank Fusion)
    fused_results = reciprocal_rank_fusion(all_results, k=60)
    
    stages["fusion"] = {
        "method": "RRF",
        "input_count": len(all_results),
        "output_count": len(fused_results)
    }
    
    # 5. 重排序
    if fused_results:
        from services.knowledge.rerank.main import rerank_documents
        final_results = await rerank_documents(
            query=translated_query,
            documents=fused_results,
            top_k=rerank_top_k
        )
    else:
        final_results = []
    
    total_time_ms = (datetime.now() - start_time).total_seconds() * 1000
    
    stats = {
        "total_time_ms": total_time_ms,
        "stages": stages,
        "queries_used": all_queries
    }
    
    return final_results, stats


def reciprocal_rank_fusion(
    results: List[Dict[str, Any]],
    k: int = 60
) -> List[Dict[str, Any]]:
    """
    Reciprocal Rank Fusion (RRF) 结果融合
    
    将多个查询的结果融合为一个排序列表
    """
    # 按查询分组结果
    query_results: Dict[str, List[Dict[str, Any]]] = {}
    
    for result in results:
        query_key = result.get("query", "default")
        if query_key not in query_results:
            query_results[query_key] = []
        query_results[query_key].append(result)
    
    # 计算 RRF 分数
    rrf_scores: Dict[str, float] = {}
    doc_map: Dict[str, Dict[str, Any]] = {}
    
    for query, docs in query_results.items():
        for rank, doc in enumerate(docs):
            doc_id = doc.get("doc_id", id(doc))
            
            # RRF 公式：1 / (k + rank)
            rrf_score = 1.0 / (k + rank)
            
            if doc_id not in rrf_scores:
                rrf_scores[doc_id] = 0.0
                doc_map[doc_id] = doc
            
            rrf_scores[doc_id] += rrf_score
    
    # 按 RRF 分数排序
    sorted_docs = sorted(
        doc_map.values(),
        key=lambda d: rrf_scores.get(d.get("doc_id", id(d)), 0),
        reverse=True
    )
    
    # 添加融合分数
    for doc in sorted_docs:
        doc["rrf_score"] = rrf_scores.get(doc.get("doc_id", id(doc)), 0)
        doc["fusion_method"] = "RRF"
    
    return sorted_docs


# ==================== API 端点 ====================

@router.post("/search", response_model=TRRResponse)
async def trr_search(request: TRRRequest):
    """
    TRR 跨语言检索接口
    
    Translate → Retrieve → Rerank 完整流程
    """
    start_time = datetime.now()
    
    results, stats = await translate_retrieve_rerank(
        query=request.query,
        course_id=request.course_id,
        top_k=request.top_k,
        rerank_top_k=request.rerank_top_k,
        enable_translation=request.enable_translation,
        enable_hyde=request.enable_hyde,
        use_cache=request.use_cache
    )
    
    processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000
    
    return TRRResponse(
        original_query=request.query,
        translated_query=stats.get("final_query"),
        results=results,
        total_results=len(results),
        stages=stats["stages"],
        processing_time_ms=processing_time_ms
    )


@router.post("/search/expanded")
async def trr_expanded_search(request: TRRRequest):
    """
    带查询扩展的 TRR 检索接口
    
    使用多个相关查询进行检索，然后融合结果
    """
    start_time = datetime.now()
    
    results, stats = await trr_with_expansion(
        query=request.query,
        course_id=request.course_id,
        top_k=request.top_k,
        rerank_top_k=request.rerank_top_k
    )
    
    processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000
    
    return {
        "original_query": request.query,
        "results": results,
        "total_results": len(results),
        "stats": stats,
        "processing_time_ms": processing_time_ms
    }


@router.get("/stats")
async def get_trr_stats():
    """获取 TRR 服务状态"""
    return {
        "code": 200,
        "data": {
            "service": "TRR",
            "stages": ["Translate", "Retrieve", "Rerank"],
            "features": [
                "跨语言检索 (中文→英文)",
                "多查询扩展",
                "RRF 结果融合",
                "Cross-Encoder 重排序"
            ]
        }
    }


# ==================== 便捷函数 ====================

async def trr_search_simple(
    query: str,
    course_id: Optional[str] = None,
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    便捷函数：TRR 检索
    
    用于在其他服务中直接调用
    """
    results, _ = await translate_retrieve_rerank(
        query=query,
        course_id=course_id,
        top_k=top_k * 2,  # 检索更多，然后重排序
        rerank_top_k=top_k,
        enable_translation=True
    )
    return results
