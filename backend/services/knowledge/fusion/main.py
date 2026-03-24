"""多路结果融合 (FUSION) - RRF + 加权融合 + 去重 + 缓存优化"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib
import json

router = APIRouter(prefix="/fusion", tags=["Result Fusion"])

# ==================== 配置参数 ====================
# 融合权重配置 - P11 优化：针对跨语言检索场景优化
# 诊断报告建议：中文查询 vs 英文文档，需要平衡语义和关键词检索
FUSION_WEIGHTS = {
    "semantic": 0.55,  # P11 优化：提升至 0.55，跨语言场景下语义检索更重要
    "keyword": 0.35,  # 保持 0.35，关键词匹配对技术术语检索有效
    "graph": 0.10     # 降低至 0.10，图谱检索作为补充
}

# 跨语言检索权重配置（当检测到中文查询时）
CROSS_LANGUAGE_WEIGHTS = {
    "semantic": 0.60,  # 跨语言场景下，更重视语义检索
    "keyword": 0.30,  # 关键词检索作为补充
    "graph": 0.10
}

# 去重阈值
DEDUPLICATION_THRESHOLD = 0.85

# RRF 参数
RRF_K = 60  # RRF 常数，通常在 60 左右

# 缓存配置
CACHE_TTL = 3600  # 缓存过期时间 (秒)
MAX_CACHE_SIZE = 1000  # 最大缓存条目数


# ==================== 数据模型 ====================
class FusionRequest(BaseModel):
    channel_results: Dict[str, List[Dict]]
    weights: Dict[str, float] = FUSION_WEIGHTS
    top_k: int = 10
    use_deduplication: bool = True
    use_rrf: bool = True  # 是否使用 RRF 融合
    rrf_k: int = RRF_K
    query: Optional[str] = None  # 查询内容，用于缓存键计算


class FusionRequestSimple(BaseModel):
    """简化版融合请求"""
    results: List[List[Dict]] = []
    query: Optional[str] = None
    top_k: int = 10


class CacheEntry(BaseModel):
    """缓存条目"""
    result: List[Dict]
    created_at: datetime
    hits: int = 0


# ==================== 缓存系统 ====================
# 本地 LRU 缓存
_fusion_cache: Dict[str, CacheEntry] = {}
_cache_stats = {"hits": 0, "misses": 0, "size": 0}


def compute_cache_key(query: str, channel_results: Dict[str, List[Dict]], top_k: int, use_rrf: bool) -> str:
    """
    计算缓存键 - 修复 ONL-004 问题
    
    修复前：缓存键只考虑渠道名称和数量，不考虑具体内容
    修复后：缓存键包含查询内容哈希，确保不同查询不会命中错误缓存
    
    公式：cache_key = MD5(query_hash + channels + counts + top_k + use_rrf)
    """
    # 计算查询哈希
    query_hash = hashlib.md5(query.encode()).hexdigest()
    
    key_data = {
        "query_hash": query_hash,  # 包含查询内容哈希
        "channels": sorted(channel_results.keys()),
        "counts": {k: len(v) for k, v in channel_results.items()},
        "top_k": top_k,
        "use_rrf": use_rrf
    }
    key_str = json.dumps(key_data, sort_keys=True)
    return hashlib.md5(key_str.encode()).hexdigest()


def get_from_cache(cache_key: str) -> Optional[List[Dict]]:
    """从缓存获取结果"""
    if cache_key in _fusion_cache:
        entry = _fusion_cache[cache_key]
        # 检查是否过期
        if (datetime.utcnow() - entry.created_at).total_seconds() < CACHE_TTL:
            entry.hits += 1
            _cache_stats["hits"] += 1
            return entry.result
        else:
            # 过期，删除
            del _fusion_cache[cache_key]
            _cache_stats["size"] -= 1
    _cache_stats["misses"] += 1
    return None


def save_to_cache(cache_key: str, result: List[Dict]):
    """保存结果到缓存 - LRU 策略"""
    global _fusion_cache
    
    # 如果缓存已满，删除最久未使用的条目
    if len(_fusion_cache) >= MAX_CACHE_SIZE:
        oldest_key = min(_fusion_cache.keys(), key=lambda k: _fusion_cache[k].created_at)
        del _fusion_cache[oldest_key]
        _cache_stats["size"] -= 1
    
    _fusion_cache[cache_key] = CacheEntry(
        result=result,
        created_at=datetime.utcnow()
    )
    _cache_stats["size"] += 1


# ==================== 核心融合算法 ====================
def rrf_fuse(channel_results: Dict[str, List[Dict]], k: int = RRF_K, top_k: int = 10) -> List[Dict]:
    """
    Reciprocal Rank Fusion (RRF) 融合算法 - 优化版
    
    公式：RRF(d) = Σ 1/(k + rank(d))
    
    参数:
        channel_results: 各渠道的检索结果 {channel_name: [docs]}
        k: RRF 常数，用于调节排名影响 (默认 60)
        top_k: 返回前 K 个结果
    
    返回:
        融合后的结果列表
    
    优势:
        - 无需分数归一化
        - 对不同检索系统的分数尺度不敏感
        - 简单高效，已被证明在 RAG 系统中效果优秀
    """
    rrf_scores: Dict[str, Dict] = {}
    
    for channel, results in channel_results.items():
        for rank, doc in enumerate(results):
            # 生成文档唯一 ID
            doc_id = doc.get("doc_id", doc.get("id", str(hash(doc.get("content", "")))))
            
            if doc_id not in rrf_scores:
                rrf_scores[doc_id] = {
                    "doc": doc.copy(),
                    "rrf_score": 0.0,
                    "channels": [],
                    "ranks": {}
                }
            
            # RRF 分数累加：1/(k + rank + 1)
            rrf_scores[doc_id]["rrf_score"] += 1.0 / (k + rank + 1)
            rrf_scores[doc_id]["channels"].append(channel)
            rrf_scores[doc_id]["ranks"][channel] = rank + 1
    
    # 转换为列表并排序
    fused_results = []
    for doc_id, data in rrf_scores.items():
        result = data["doc"]
        result["final_score"] = data["rrf_score"]
        result["channels"] = data["channels"]
        result["ranks"] = data["ranks"]
        result["fusion_method"] = "rrf"
        fused_results.append(result)
    
    # 按 RRF 分数降序排序
    fused_results.sort(key=lambda x: x.get("final_score", 0), reverse=True)
    
    return fused_results[:top_k]


def weighted_fuse(channel_results: Dict[str, List[Dict]], weights: Dict[str, float], top_k: int = 10) -> List[Dict]:
    """
    加权融合算法（优化版）
    
    包含 Min-Max 归一化和权重调整
    """
    all_results = []
    
    for channel, results in channel_results.items():
        normalized = normalize_scores(results, channel)
        weight = weights.get(channel, 0.33)
        
        for r in normalized:
            fused_result = r.copy()
            normalized_score = r.get(f"{channel}_normalized", 0)
            fused_result["final_score"] = normalized_score * weight
            fused_result["channel"] = channel
            fused_result["fusion_method"] = "weighted"
            all_results.append(fused_result)
    
    all_results.sort(key=lambda x: x.get("final_score", 0), reverse=True)
    
    return all_results[:top_k]


def hybrid_fuse(channel_results: Dict[str, List[Dict]], weights: Dict[str, float], k: int = RRF_K, top_k: int = 10) -> List[Dict]:
    """
    混合融合算法：RRF + 权重调整
    
    结合 RRF 的排名优势和权重调整的灵活性
    """
    # 先用 RRF 融合
    rrf_results = rrf_fuse(channel_results, k=k, top_k=top_k * 2)
    
    # 再根据权重调整分数
    for result in rrf_results:
        channels = result.get("channels", [])
        channel_weights = [weights.get(ch, 0.33) for ch in channels]
        # 多路召回加分
        multi_channel_bonus = len(channels) * 0.1
        result["final_score"] = result.get("final_score", 0) * sum(channel_weights) / len(channel_weights) + multi_channel_bonus
        result["fusion_method"] = "hybrid"
    
    # 重新排序
    rrf_results.sort(key=lambda x: x.get("final_score", 0), reverse=True)
    
    return rrf_results[:top_k]


# ==================== 辅助函数 ====================
def normalize_scores(results: List[Dict], channel: str) -> List[Dict]:
    """Min-Max 归一化分数"""
    if not results:
        return results

    scores = [r.get("score", 0) for r in results]
    min_score = min(scores)
    max_score = max(scores)

    if max_score - min_score == 0:
        return results

    normalized = []
    for r in results:
        new_r = r.copy()
        new_r[f"{channel}_normalized"] = (r.get("score", 0) - min_score) / (max_score - min_score)
        normalized.append(new_r)

    return normalized


def compute_semantic_similarity(content1: str, content2: str) -> float:
    """计算语义相似度（Jaccard 相似度）"""
    # 使用字符级 n-gram 提高中文支持
    def get_ngrams(text: str, n: int = 2) -> set:
        return set(text[i:i+n] for i in range(len(text) - n + 1))
    
    ngrams1 = get_ngrams(content1.lower())
    ngrams2 = get_ngrams(content2.lower())

    if not ngrams1 or not ngrams2:
        return 0.0

    intersection = ngrams1 & ngrams2
    union = ngrams1 | ngrams2

    return len(intersection) / len(union) if union else 0.0


def deduplicate_results(results: List[Dict], threshold: float = 0.85) -> List[Dict]:
    """基于语义相似度去重（优化版）"""
    if not results:
        return results

    deduplicated = []
    seen_contents = []

    for result in results:
        is_duplicate = False
        content = result.get("content", "")

        for seen_content in seen_contents:
            sim = compute_semantic_similarity(content, seen_content)
            if sim > threshold:
                is_duplicate = True
                break

        if not is_duplicate:
            deduplicated.append(result)
            seen_contents.append(content)

    return deduplicated


def fuse_results(request: FusionRequest) -> List[Dict]:
    """融合多路结果（主函数）"""

    # 1. 检查缓存 - 修复 ONL-004: 缓存键必须包含查询内容
    # 从 channel_results 中提取查询内容 (如果有)
    query = ""
    if hasattr(request, 'query') and request.query:
        query = request.query
    else:
        # 如果没有 query 字段，使用各渠道第一个文档的内容哈希作为代理
        query_parts = []
        for channel, results in request.channel_results.items():
            if results:
                query_parts.append(f"{channel}:{results[0].get('doc_id', '')}")
        query = "|".join(query_parts)
    
    cache_key = compute_cache_key(query, request.channel_results, request.top_k, request.use_rrf)
    cached_result = get_from_cache(cache_key)
    if cached_result:
        return cached_result
    
    # 2. 选择融合策略
    if request.use_rrf:
        # 使用 RRF 融合
        fused = hybrid_fuse(
            request.channel_results,
            weights=request.weights,
            k=request.rrf_k,
            top_k=request.top_k * 2  # 先多保留一些
        )
    else:
        # 使用加权融合
        fused = weighted_fuse(
            request.channel_results,
            weights=request.weights,
            top_k=request.top_k * 2
        )
    
    # 3. 去重
    if request.use_deduplication:
        fused = deduplicate_results(fused, DEDUPLICATION_THRESHOLD)
    
    # 4. 截取 Top-K
    fused = fused[:request.top_k]
    
    # 5. 保存到缓存
    save_to_cache(cache_key, fused)
    
    return fused


# ==================== API 接口 ====================
@router.post("/combine")
async def fuse_results_endpoint(request: FusionRequest):
    """结果融合接口 - 支持 RRF 和加权融合"""
    fused = fuse_results(request)

    return {
        "code": 200,
        "message": "success",
        "data": {
            "results": fused,
            "total": len(fused),
            "weights_used": request.weights,
            "fusion_method": "rrf" if request.use_rrf else "weighted",
            "cache_stats": _cache_stats
        }
    }


@router.post("/combine/simple")
async def fuse_results_simple(request: FusionRequestSimple):
    """简化版结果融合"""
    # 将 results 列表转换为 channel_results 格式
    channel_results = {}
    for i, result_list in enumerate(request.results):
        channel_results[f"channel_{i}"] = result_list

    simple_request = FusionRequest(
        channel_results=channel_results,
        top_k=request.top_k
    )
    fused = fuse_results(simple_request)

    return {
        "code": 200,
        "message": "success",
        "data": {
            "results": fused,
            "total": len(fused)
        }
    }


@router.get("/config")
async def get_fusion_config():
    """获取融合配置"""
    return {
        "code": 200,
        "data": {
            "weights": FUSION_WEIGHTS,
            "deduplication_threshold": DEDUPLICATION_THRESHOLD,
            "rrf_k": RRF_K,
            "cache_config": {
                "ttl": CACHE_TTL,
                "max_size": MAX_CACHE_SIZE
            }
        }
    }


@router.post("/config")
async def update_fusion_config(
    weights: Optional[Dict[str, float]] = None,
    deduplication_threshold: Optional[float] = None,
    rrf_k: Optional[int] = None
):
    """更新融合配置"""
    global FUSION_WEIGHTS, DEDUPLICATION_THRESHOLD, RRF_K
    
    if weights:
        FUSION_WEIGHTS.update(weights)
    if deduplication_threshold is not None:
        DEDUPLICATION_THRESHOLD = deduplication_threshold
    if rrf_k is not None:
        RRF_K = rrf_k
    
    return {"code": 200, "message": "配置已更新", "data": {
        "weights": FUSION_WEIGHTS,
        "deduplication_threshold": DEDUPLICATION_THRESHOLD,
        "rrf_k": RRF_K
    }}


@router.get("/cache/stats")
async def get_cache_stats():
    """获取缓存统计"""
    return {
        "code": 200,
        "data": {
            "stats": _cache_stats,
            "hit_rate": _cache_stats["hits"] / max(_cache_stats["hits"] + _cache_stats["misses"], 1)
        }
    }


@router.delete("/cache/clear")
async def clear_cache():
    """清空缓存"""
    global _fusion_cache, _cache_stats
    _fusion_cache = {}
    _cache_stats = {"hits": 0, "misses": 0, "size": 0}
    return {"code": 200, "message": "缓存已清空"}
