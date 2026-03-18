"""多路结果融合 (FUSION) - 加权融合 + 去重"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np

router = APIRouter(prefix="/fusion", tags=["Result Fusion"])

# 融合权重配置
FUSION_WEIGHTS = {
    "semantic": 0.4,
    "keyword": 0.3,
    "graph": 0.3
}

# 去重阈值
DEDUPLICATION_THRESHOLD = 0.85


class FusionRequest(BaseModel):
    channel_results: Dict[str, List[Dict]]
    weights: Dict[str, float] = FUSION_WEIGHTS
    top_k: int = 10
    use_deduplication: bool = True


class FusionRequestSimple(BaseModel):
    """简化版融合请求"""
    results: List[List[Dict]] = []
    query: Optional[str] = None
    top_k: int = 10


def normalize_scores(results: List[Dict], channel: str) -> List[Dict]:
    """Min-Max归一化分数"""
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
    """计算语义相似度（简化版）"""
    words1 = set(content1.lower().split())
    words2 = set(content2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1 & words2
    union = words1 | words2
    
    return len(intersection) / len(union)


def deduplicate_results(results: List[Dict], threshold: float = 0.85) -> List[Dict]:
    """基于语义相似度去重"""
    if not results:
        return results
    
    deduplicated = []
    
    for result in results:
        is_duplicate = False
        
        for existing in deduplicated:
            content1 = result.get("content", "")
            content2 = existing.get("content", "")
            
            if content1 and content2:
                sim = compute_semantic_similarity(content1, content2)
                if sim > threshold:
                    is_duplicate = True
                    break
        
        if not is_duplicate:
            deduplicated.append(result)
    
    return deduplicated


def fuse_results(request: FusionRequest) -> List[Dict]:
    """融合多路结果"""
    all_results = []
    
    for channel, results in request.channel_results.items():
        normalized = normalize_scores(results, channel)
        weight = request.weights.get(channel, 0)
        
        for r in normalized:
            fused_result = r.copy()
            normalized_score = r.get(f"{channel}_normalized", 0)
            fused_result["final_score"] = normalized_score * weight
            fused_result["channel"] = channel
            all_results.append(fused_result)
    
    if request.use_deduplication:
        all_results = deduplicate_results(all_results, DEDUPLICATION_THRESHOLD)
    
    all_results.sort(key=lambda x: x.get("final_score", 0), reverse=True)
    
    return all_results[:request.top_k]


@router.post("/combine")
async def fuse_results_endpoint(request: FusionRequest):
    """结果融合接口"""
    fused = fuse_results(request)
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "results": fused,
            "total": len(fused),
            "weights_used": request.weights
        }
    }


@router.post("/combine/simple")
async def fuse_results_simple(request: FusionRequestSimple):
    """简化版结果融合"""
    # 将results列表转换为channel_results格式
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
    return {
        "code": 200,
        "data": {
            "weights": FUSION_WEIGHTS,
            "deduplication_threshold": DEDUPLICATION_THRESHOLD
        }
    }


@router.post("/config")
async def update_fusion_config(weights: Dict[str, float] = FUSION_WEIGHTS):
    global FUSION_WEIGHTS
    FUSION_WEIGHTS.update(weights)
    return {"code": 200, "message": "配置已更新", "data": {"weights": FUSION_WEIGHTS}}
