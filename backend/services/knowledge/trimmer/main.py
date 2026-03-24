"""上下文修剪与压缩服务 - 智能 token 预算优化 + MMR 多样性选择"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import re
import numpy as np

router = APIRouter(prefix="/trimmer", tags=["Context Trimmer"])

# ==================== 配置 ====================
DEFAULT_MAX_TOKENS = 3000  # 默认最大 token 数
DEFAULT_CHUNK_TOKENS = 500  # 每个文档块平均 token 数
CHINESE_TOKEN_RATIO = 1.5  # 中文 token 比例 (1.5 字符/token)
ENGLISH_TOKEN_RATIO = 4  # 英文 token 比例 (4 字符/token)

# MMR 配置 - P11 优化：提升相关性权重
DEFAULT_MMR_LAMBDA = 0.75  # P11 优化：从 0.5 提升至 0.75，更重视相关性

# 智能压缩配置
MIN_CONTEXT_TOKENS = 500  # 最小上下文 token 数
SENTENCE_MIN_LENGTH = 20  # 句子最小长度


class TrimmerRequest(BaseModel):
    """修剪请求"""
    documents: List[Dict[str, Any]]
    query: Optional[str] = None
    max_tokens: int = DEFAULT_MAX_TOKENS
    strategy: str = "score_priority"  # score_priority, diversity, recency
    use_mmr: bool = True  # 是否使用 MMR 多样性选择
    mmr_lambda: float = DEFAULT_MMR_LAMBDA


class TrimmerResponse(BaseModel):
    """修剪响应"""
    trimmed_documents: List[Dict[str, Any]]
    total_tokens: int
    compression_ratio: float
    strategy_used: str


class MMRRequest(BaseModel):
    """MMR 多样性选择请求"""
    documents: List[Dict[str, Any]]
    query: Optional[str] = None
    top_k: int = 10
    lambda_param: float = 0.5  # MMR 平衡参数


def estimate_tokens(text: str) -> int:
    """
    估算文本的 token 数量
    
    中文约 1.5 字符/token，英文约 4 字符/token
    """
    if not text:
        return 0
    
    # 统计中文字符和英文字符
    chinese_chars = len(re.findall(r'[\u4e00-\u9fa5]', text))
    english_chars = len(re.findall(r'[a-zA-Z]+', text))
    other_chars = len(text) - chinese_chars - english_chars
    
    # 估算 token 数
    tokens = (chinese_chars / CHINESE_TOKEN_RATIO + 
              english_chars / ENGLISH_TOKEN_RATIO + 
              other_chars / 10)
    
    return int(tokens)


def compute_text_similarity(text1: str, text2: str) -> float:
    """
    计算两个文本的相似度 (Jaccard 相似度)
    """
    if not text1 or not text2:
        return 0.0
    
    # 分词 (简单按空格和标点分割)
    words1 = set(re.findall(r'[\u4e00-\u9fa5]{2,}|[a-zA-Z]{3,}', text1.lower()))
    words2 = set(re.findall(r'[\u4e00-\u9fa5]{2,}|[a-zA-Z]{3,}', text2.lower()))
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1 & words2
    union = words1 | words2
    
    return len(intersection) / len(union) if union else 0.0


def mmr_select(
    documents: List[Dict[str, Any]],
    query: Optional[str],
    top_k: int,
    lambda_param: float = 0.5
) -> List[Dict[str, Any]]:
    """
    MMR (Maximal Marginal Relevance) 多样性选择
    
    平衡相关性和多样性，避免选择过于相似的文档
    
    Args:
        documents: 候选文档列表
        query: 查询文本
        top_k: 选择数量
        lambda_param: 平衡参数 (0-1)，越大越重视相关性
    
    Returns:
        选中的文档列表
    """
    if not documents:
        return []
    
    if top_k >= len(documents):
        return documents
    
    # 计算每个文档与查询的相关性分数
    query_relevance = {}
    if query:
        query_words = set(re.findall(r'[\u4e00-\u9fa5]{2,}|[a-zA-Z]{3,}', query.lower()))
        for i, doc in enumerate(documents):
            content = doc.get("content", "")
            doc_words = set(re.findall(r'[\u4e00-\u9fa5]{2,}|[a-zA-Z]{3,}', content.lower()))
            
            # Jaccard 相似度
            if doc_words and query_words:
                sim = len(query_words & doc_words) / len(query_words | doc_words)
            else:
                sim = 0.0
            
            # 结合原始分数
            original_score = doc.get("score", 0) or doc.get("final_score", 0)
            query_relevance[i] = lambda_param * original_score + (1 - lambda_param) * sim
    else:
        # 没有查询时，只使用原始分数
        for i, doc in enumerate(documents):
            query_relevance[i] = doc.get("score", 0) or doc.get("final_score", 0)
    
    # MMR 选择
    selected = []
    remaining = set(range(len(documents)))
    
    while len(selected) < top_k and remaining:
        best_score = -float('inf')
        best_idx = None
        
        for idx in remaining:
            # 相关性分数
            rel_score = query_relevance[idx]
            
            # 多样性分数 (与已选文档的最小相似度)
            if selected:
                min_sim = min(
                    compute_text_similarity(
                        documents[idx].get("content", ""),
                        documents[s].get("content", "")
                    )
                    for s in selected
                )
            else:
                min_sim = 0
            
            # MMR 分数
            mmr_score = lambda_param * rel_score - (1 - lambda_param) * min_sim
            
            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = idx
        
        if best_idx is not None:
            selected.append(best_idx)
            remaining.remove(best_idx)
    
    return [documents[i] for i in selected]


def truncate_content(content: str, max_tokens: int) -> str:
    """
    截断内容到指定 token 数
    """
    if not content:
        return ""
    
    current_tokens = estimate_tokens(content)
    
    if current_tokens <= max_tokens:
        return content
    
    # 按比例截断
    ratio = max_tokens / current_tokens
    truncate_len = int(len(content) * ratio)
    
    # 确保在句子边界截断
    truncated = content[:truncate_len]
    for sep in ['。\n', '。\n\n', '.', '\n\n', '\n']:
        last_sep = truncated.rfind(sep)
        if last_sep > len(truncated) * 0.8:
            truncated = truncated[:last_sep + len(sep)]
            break
    
    return truncated.strip()


def trim_by_score_priority(
    documents: List[Dict[str, Any]],
    max_tokens: int
) -> Tuple[List[Dict[str, Any]], int]:
    """
    按分数优先级修剪
    
    优先保留分数高的文档
    """
    # 按分数排序
    sorted_docs = sorted(
        documents,
        key=lambda x: x.get("score", 0) or x.get("final_score", 0),
        reverse=True
    )
    
    trimmed = []
    total_tokens = 0
    
    for doc in sorted_docs:
        content = doc.get("content", "")
        doc_tokens = estimate_tokens(content)
        
        if total_tokens + doc_tokens <= max_tokens:
            trimmed.append(doc)
            total_tokens += doc_tokens
        elif total_tokens < max_tokens:
            # 截断文档
            remaining_tokens = max_tokens - total_tokens
            if remaining_tokens > 100:  # 至少保留 100 token
                truncated = truncate_content(content, remaining_tokens)
                doc_copy = doc.copy()
                doc_copy["content"] = truncated
                doc_copy["truncated"] = True
                trimmed.append(doc_copy)
                total_tokens += estimate_tokens(truncated)
            break
        else:
            break
    
    return trimmed, total_tokens


def trim_by_diversity(
    documents: List[Dict[str, Any]],
    query: Optional[str],
    max_tokens: int,
    lambda_param: float = 0.5
) -> Tuple[List[Dict[str, Any]], int]:
    """
    按多样性修剪
    
    使用 MMR 选择多样且相关的文档
    """
    # 估算需要的文档数量
    avg_doc_tokens = sum(estimate_tokens(d.get("content", "")) for d in documents) / max(len(documents), 1)
    estimated_k = int(max_tokens / avg_doc_tokens) if avg_doc_tokens > 0 else len(documents)
    
    # MMR 选择
    selected = mmr_select(documents, query, estimated_k, lambda_param)
    
    # 计算总 token 数
    trimmed = []
    total_tokens = 0
    
    for doc in selected:
        content = doc.get("content", "")
        doc_tokens = estimate_tokens(content)
        
        if total_tokens + doc_tokens <= max_tokens:
            trimmed.append(doc)
            total_tokens += doc_tokens
        elif total_tokens < max_tokens:
            remaining_tokens = max_tokens - total_tokens
            if remaining_tokens > 100:
                truncated = truncate_content(content, remaining_tokens)
                doc_copy = doc.copy()
                doc_copy["content"] = truncated
                doc_copy["truncated"] = True
                trimmed.append(doc_copy)
                total_tokens += estimate_tokens(truncated)
    
    return trimmed, total_tokens


def trim_context(
    documents: List[Dict[str, Any]],
    query: Optional[str] = None,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    strategy: str = "score_priority"
) -> Tuple[List[Dict[str, Any]], int]:
    """
    修剪上下文
    
    Args:
        documents: 候选文档列表
        query: 查询文本
        max_tokens: 最大 token 数
        strategy: 修剪策略
    
    Returns:
        (修剪后的文档列表，总 token 数)
    """
    if not documents:
        return [], 0
    
    if strategy == "diversity":
        return trim_by_diversity(documents, query, max_tokens)
    elif strategy == "recency":
        # 按时间倒序 (假设有 created_at 字段)
        sorted_docs = sorted(
            documents,
            key=lambda x: x.get("created_at", ""),
            reverse=True
        )
        return trim_by_score_priority(sorted_docs, max_tokens)
    else:  # score_priority
        return trim_by_score_priority(documents, max_tokens)


def build_context_string(
    documents: List[Dict[str, Any]],
    template: str = "参考{index}: {content}"
) -> str:
    """
    构建上下文字符串
    
    Args:
        documents: 修剪后的文档列表
        template: 模板字符串
    
    Returns:
        格式化的上下文字符串
    """
    context_parts = []
    
    for i, doc in enumerate(documents):
        content = doc.get("content", "")
        formatted = template.format(
            index=i + 1,
            content=content,
            **doc
        )
        context_parts.append(formatted)
    
    return "\n\n".join(context_parts)


@router.post("/trim", response_model=TrimmerResponse)
async def trim_documents(request: TrimmerRequest):
    """修剪文档上下文"""
    start_time = datetime.now()
    
    original_tokens = sum(estimate_tokens(d.get("content", "")) for d in request.documents)
    
    trimmed, total_tokens = trim_context(
        documents=request.documents,
        query=request.query,
        max_tokens=request.max_tokens,
        strategy=request.strategy
    )
    
    processing_time = (datetime.now() - start_time).total_seconds()
    compression_ratio = total_tokens / original_tokens if original_tokens > 0 else 0
    
    return TrimmerResponse(
        trimmed_documents=trimmed,
        total_tokens=total_tokens,
        compression_ratio=round(compression_ratio, 3),
        strategy_used=request.strategy
    )


@router.post("/mmr")
async def mmr_select_endpoint(request: MMRRequest):
    """MMR 多样性选择"""
    selected = mmr_select(
        documents=request.documents,
        query=request.query,
        top_k=request.top_k,
        lambda_param=request.lambda_param
    )
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "selected_count": len(selected),
            "documents": selected,
            "lambda_param": request.lambda_param
        }
    }


@router.post("/estimate")
async def estimate_tokens_endpoint(text: str):
    """估算 token 数量"""
    tokens = estimate_tokens(text)
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "text_length": len(text),
            "estimated_tokens": tokens,
            "chinese_ratio": len(re.findall(r'[\u4e00-\u9fa5]', text)) / max(len(text), 1)
        }
    }


@router.post("/truncate")
async def truncate_endpoint(text: str, max_tokens: int):
    """截断文本"""
    truncated = truncate_content(text, max_tokens)
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "original_length": len(text),
            "original_tokens": estimate_tokens(text),
            "truncated_length": len(truncated),
            "truncated_tokens": estimate_tokens(truncated),
            "truncated_text": truncated
        }
    }


@router.post("/build-context")
async def build_context(
    documents: List[Dict[str, Any]],
    template: str = "参考{index}: {content}"
):
    """构建上下文字符串"""
    context = build_context_string(documents, template)
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "context": context,
            "total_tokens": estimate_tokens(context),
            "doc_count": len(documents)
        }
    }


@router.get("/config")
async def get_config():
    """获取配置"""
    return {
        "code": 200,
        "data": {
            "max_tokens": DEFAULT_MAX_TOKENS,
            "chunk_tokens": DEFAULT_CHUNK_TOKENS,
            "strategies": ["score_priority", "diversity", "recency"],
            "token_estimation": {
                "chinese_ratio": CHINESE_TOKEN_RATIO,
                "english_ratio": ENGLISH_TOKEN_RATIO
            },
            "mmr_config": {
                "default_lambda": DEFAULT_MMR_LAMBDA,
                "description": "λ越大越重视相关性，越小越重视多样性"
            },
            "compression_config": {
                "min_tokens": MIN_CONTEXT_TOKENS,
                "sentence_min_length": SENTENCE_MIN_LENGTH
            }
        }
    }


# ==================== 增强的智能压缩功能 ====================
def extract_key_sentences(content: str, query: Optional[str] = None, max_sentences: int = 5) -> List[str]:
    """
    提取关键句子
    
    基于查询相关性和句子重要性提取关键句子
    """
    if not content:
        return []
    
    # 分割句子 (支持中英文)
    sentences = re.split(r'(?<=[。！？.!?])\s*', content)
    sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > SENTENCE_MIN_LENGTH]
    
    if not sentences:
        return sentences
    
    if not query:
        # 没有查询时，返回前 max_sentences 个句子
        return sentences[:max_sentences]
    
    # 计算每个句子与查询的相关性
    query_words = set(re.findall(r'[\u4e00-\u9fa5]{2,}|[a-zA-Z]{3,}', query.lower()))
    sentence_scores = []
    
    for i, sentence in enumerate(sentences):
        sentence_words = set(re.findall(r'[\u4e00-\u9fa5]{2,}|[a-zA-Z]{3,}', sentence.lower()))
        
        # Jaccard 相似度
        if sentence_words and query_words:
            sim = len(query_words & sentence_words) / len(query_words | sentence_words)
        else:
            sim = 0.0
        
        # 位置加分 (前面的句子更重要)
        position_bonus = 1.0 / (i + 1) * 0.3
        
        sentence_scores.append((i, sim + position_bonus))
    
    # 排序并选择 top 句子
    sentence_scores.sort(key=lambda x: x[1], reverse=True)
    selected_indices = sorted([idx for idx, _ in sentence_scores[:max_sentences]])
    
    return [sentences[i] for i in selected_indices]


def smart_compress_content(content: str, query: Optional[str] = None, target_tokens: int = 300) -> str:
    """
    智能压缩内容
    
    策略:
    1. 提取关键句子
    2. 保留段落结构
    3. 去除冗余信息
    """
    if not content:
        return ""
    
    current_tokens = estimate_tokens(content)
    
    if current_tokens <= target_tokens:
        return content
    
    # 提取关键句子
    key_sentences = extract_key_sentences(content, query, max_sentences=10)
    
    if not key_sentences:
        return content[:int(len(content) * target_tokens / current_tokens)]
    
    # 组合关键句子
    compressed = " ".join(key_sentences)
    compressed_tokens = estimate_tokens(compressed)
    
    # 如果还是超过目标，继续压缩
    if compressed_tokens > target_tokens:
        ratio = target_tokens / compressed_tokens
        compressed = compressed[:int(len(compressed) * ratio)]
    
    return compressed


def compress_documents(
    documents: List[Dict[str, Any]],
    query: Optional[str] = None,
    max_tokens: int = DEFAULT_MAX_TOKENS
) -> Tuple[List[Dict[str, Any]], int]:
    """
    压缩文档列表
    
    对每个文档进行智能压缩，保证总 token 数不超过限制
    """
    if not documents:
        return [], 0
    
    # 计算平均每个文档可分配的 token 数
    avg_tokens_per_doc = max_tokens // len(documents)
    avg_tokens_per_doc = max(avg_tokens_per_doc, MIN_CONTEXT_TOKENS // len(documents))
    
    compressed_docs = []
    total_tokens = 0
    
    for doc in documents:
        content = doc.get("content", "")
        doc_copy = doc.copy()
        
        # 智能压缩
        compressed_content = smart_compress_content(content, query, avg_tokens_per_doc)
        doc_copy["content"] = compressed_content
        doc_copy["compressed"] = True
        doc_copy["original_length"] = len(content)
        doc_copy["compressed_length"] = len(compressed_content)
        
        compressed_docs.append(doc_copy)
        total_tokens += estimate_tokens(compressed_content)
    
    return compressed_docs, total_tokens


@router.post("/smart-compress")
async def smart_compress_endpoint(
    documents: List[Dict[str, Any]],
    query: Optional[str] = None,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    use_mmr: bool = True,
    mmr_lambda: float = DEFAULT_MMR_LAMBDA
):
    """
    智能压缩文档
    
    结合 MMR 多样性选择和智能内容压缩
    """
    original_tokens = sum(estimate_tokens(d.get("content", "")) for d in documents)
    
    # 1. 先使用 MMR 选择重要文档
    if use_mmr and len(documents) > 5:
        selected_docs = mmr_select(
            documents=documents,
            query=query,
            top_k=min(10, len(documents)),
            lambda_param=mmr_lambda
        )
    else:
        selected_docs = documents
    
    # 2. 智能压缩
    compressed_docs, total_tokens = compress_documents(
        documents=selected_docs,
        query=query,
        max_tokens=max_tokens
    )
    
    compression_ratio = total_tokens / original_tokens if original_tokens > 0 else 0
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "compressed_documents": compressed_docs,
            "original_tokens": original_tokens,
            "compressed_tokens": total_tokens,
            "compression_ratio": round(compression_ratio, 3),
            "doc_count": len(compressed_docs),
            "mmr_applied": use_mmr
        }
    }


@router.get("/optimization/tips")
async def get_optimization_tips():
    """获取上下文优化建议"""
    return {
        "code": 200,
        "data": {
            "strategies": {
                "score_priority": {
                    "description": "按分数优先级，适合通用场景",
                    "use_when": "需要保留最相关的文档"
                },
                "diversity": {
                    "description": "MMR 多样性选择，避免结果过于相似",
                    "use_when": "需要多样化的参考信息",
                    "lambda_tuning": {
                        "0.8-1.0": "高度重视相关性",
                        "0.5-0.7": "平衡相关性和多样性 (推荐)",
                        "0.0-0.4": "高度重视多样性"
                    }
                },
                "recency": {
                    "description": "按时间倒序，适合时效性内容",
                    "use_when": "最新信息更重要"
                }
            },
            "compression_tips": [
                "使用 MMR 先选择重要文档，再压缩内容",
                "保持句子完整性，避免在句子中间截断",
                "保留关键实体和数字信息",
                "对于代码内容，保留函数定义和关键逻辑"
            ],
            "token_budget": {
                "min_tokens": MIN_CONTEXT_TOKENS,
                "recommended_tokens": 2000,
                "max_tokens": DEFAULT_MAX_TOKENS
            }
        }
    }
