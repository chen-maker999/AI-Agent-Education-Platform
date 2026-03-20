"""BM25 关键词检索服务 - 传统信息检索算法"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import math
from common.core.config import settings

router = APIRouter(prefix="/search/bm25", tags=["BM25 Keyword Search"])


def _jieba():
    import jieba
    return jieba

# BM25 参数
BM25_K1 = 1.5  # 词频饱和参数
BM25_B = 0.75  # 文档长度归一化参数

# 文档集合
doc_tokens: List[List[str]] = []
doc_contents: List[str] = []
doc_id_list: List[str] = []

# 预计算参数
avg_doc_length: float = 0.0
doc_lengths: List[int] = []
idf: Dict[str, float] = {}


class BM25SearchRequest(BaseModel):
    """BM25搜索请求"""
    query: str
    top_k: int = 10


class BM25BuildRequest(BaseModel):
    """BM25构建请求"""
    documents: List[str]
    doc_ids: Optional[List[str]] = None


def tokenize(text: str) -> List[str]:
    """中文分词"""
    jieba = _jieba()
    words = jieba.cut(text)
    stopwords = {'的', '是', '在', '和', '了', '有', '我', '你', '他', '她', '它', '们',
                 '这', '那', '个', '与', '或', '及', '等', '为', '以', '于', '也', '就',
                 '都', '而', '着', '一个', '没有', '我们', '你们', '可以', '进行', '使用',
                 '该', '此', '其', '将', '被', '由', '对', '以', '及', '所', '把', '用'}
    return [w for w in words if w.strip() and len(w) > 1 and w not in stopwords]


def compute_idf() -> Dict[str, float]:
    """计算IDF值"""
    global doc_tokens, doc_lengths, avg_doc_length
    
    if not doc_tokens:
        return {}
    
    N = len(doc_tokens)
    idf_dict = {}
    doc_count = {}
    
    for tokens in doc_tokens:
        for token in set(tokens):
            doc_count[token] = doc_count.get(token, 0) + 1
    
    for token, df in doc_count.items():
        idf_dict[token] = math.log((N - df + 0.5) / (df + 0.5) + 1)
    
    return idf_dict


def compute_doc_lengths():
    """计算文档长度"""
    global doc_tokens, doc_lengths, avg_doc_length
    
    doc_lengths = [len(tokens) for tokens in doc_tokens]
    avg_doc_length = sum(doc_lengths) / len(doc_lengths) if doc_lengths else 0


def build_bm25_index(documents: List[str], doc_ids: Optional[List[str]] = None):
    """构建BM25索引"""
    global doc_tokens, doc_contents, doc_id_list, idf
    
    doc_contents = documents
    doc_id_list = doc_ids or [f"doc_{i}" for i in range(len(documents))]
    
    # 分词
    doc_tokens = [tokenize(doc) for doc in documents]
    
    # 计算文档长度
    compute_doc_lengths()
    
    # 计算IDF
    idf = compute_idf()
    
    print(f"BM25索引构建完成: {len(documents)} 个文档, 平均长度: {avg_doc_length:.1f}")


def bm25_score(query: str, doc_idx: int) -> float:
    """计算单个文档的BM25分数"""
    global doc_tokens, doc_lengths, avg_doc_length, idf
    
    if doc_idx >= len(doc_tokens):
        return 0.0
    
    query_tokens = tokenize(query)
    doc_token_set = set(doc_tokens[doc_idx])
    doc_length = doc_lengths[doc_idx]
    
    score = 0.0
    for token in query_tokens:
        if token in doc_token_set:
            # 计算词频
            tf = doc_tokens[doc_idx].count(token)
            
            # BM25公式
            numerator = tf * (BM25_K1 + 1)
            denominator = tf + BM25_K1 * (1 - BM25_B + BM25_B * doc_length / avg_doc_length)
            
            idf_val = idf.get(token, 0)
            score += idf_val * numerator / denominator
    
    return score


async def search_bm25(query: str, top_k: int = 10) -> List[Dict[str, Any]]:
    """BM25搜索"""
    global doc_contents, doc_id_list
    
    if not doc_contents:
        return []
    
    # 计算所有文档的BM25分数
    scores = []
    for i in range(len(doc_contents)):
        score = bm25_score(query, i)
        if score > 0:
            scores.append((i, score))
    
    # 排序
    scores.sort(key=lambda x: x[1], reverse=True)
    
    # 取top_k
    results = []
    for i, (doc_idx, score) in enumerate(scores[:top_k]):
        results.append({
            "doc_id": doc_id_list[doc_idx],
            "content": doc_contents[doc_idx][:500],
            "score": float(score),
            "rank": i + 1
        })
    
    return results


@router.post("/build")
async def build_bm25_index(request: BM25BuildRequest):
    """构建BM25索引"""
    build_bm25_index(request.documents, request.doc_ids)
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "document_count": len(request.documents),
            "avg_doc_length": avg_doc_length,
            "idf_terms": len(idf)
        }
    }


@router.post("/search")
async def search_bm25_index(request: BM25SearchRequest):
    """BM25搜索"""
    results = await search_bm25(request.query, request.top_k)
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "query": request.query,
            "results": results,
            "total": len(results)
        }
    }


@router.get("/stats")
async def get_bm25_stats():
    """获取BM25统计信息"""
    return {
        "code": 200,
        "message": "success",
        "data": {
            "document_count": len(doc_contents),
            "avg_doc_length": avg_doc_length,
            "idf_terms": len(idf)
        }
    }


@router.post("/clear")
async def clear_bm25_index():
    """清空BM25索引"""
    global doc_tokens, doc_contents, doc_id_list, avg_doc_length, doc_lengths, idf
    
    doc_tokens = []
    doc_contents = []
    doc_id_list = []
    avg_doc_length = 0.0
    doc_lengths = []
    idf = {}
    
    return {
        "code": 200,
        "message": "BM25索引已清空"
    }
