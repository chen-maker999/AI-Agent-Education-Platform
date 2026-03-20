"""TF-IDF 嵌入服务 - 本地轻量级向量化"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib
import numpy as np
import pickle
import os
from common.core.config import settings

router = APIRouter(prefix="/embedding/tfidf", tags=["TF-IDF Embedding"])

# TF-IDF 模型和向量存储
tfidf_vectorizer = None
tfidf_matrix = None
doc_id_list: List[str] = []
doc_contents: List[str] = []

# 词表
vocabulary: Dict[str, int] = {}
idf_values: Dict[str, float] = {}

# 缓存
embedding_cache: Dict[str, List[float]] = {}


class TFIDFEmbeddingRequest(BaseModel):
    """TF-IDF嵌入请求"""
    texts: List[str]
    max_features: Optional[int] = 5000


class TFIDFSearchRequest(BaseModel):
    """TF-IDF搜索请求"""
    query: str
    top_k: int = 10


def load_tfidf_model():
    """加载保存的TF-IDF模型"""
    global tfidf_vectorizer, tfidf_matrix, doc_id_list, doc_contents, vocabulary, idf_values
    
    model_path = "data/tfidf_model.pkl"
    if os.path.exists(model_path):
        try:
            with open(model_path, 'rb') as f:
                data = pickle.load(f)
                tfidf_vectorizer = data.get('vectorizer')
                tfidf_matrix = data.get('matrix')
                doc_id_list = data.get('doc_ids', [])
                doc_contents = data.get('contents', [])
                vocabulary = data.get('vocabulary', {})
                idf_values = data.get('idf', {})
            print(f"TF-IDF模型加载成功: {len(doc_contents)} 个文档")
            return True
        except Exception as e:
            print(f"加载TF-IDF模型失败: {e}")
    return False


def save_tfidf_model():
    """保存TF-IDF模型"""
    global tfidf_vectorizer, tfidf_matrix, doc_id_list, doc_contents, vocabulary, idf_values
    
    os.makedirs("data", exist_ok=True)
    model_path = "data/tfidf_model.pkl"
    
    try:
        with open(model_path, 'wb') as f:
            pickle.dump({
                'vectorizer': tfidf_vectorizer,
                'matrix': tfidf_matrix,
                'doc_ids': doc_id_list,
                'contents': doc_contents,
                'vocabulary': vocabulary,
                'idf': idf_values
            }, f)
        print(f"TF-IDF模型已保存: {model_path}")
        return True
    except Exception as e:
        print(f"保存TF-IDF模型失败: {e}")
        return False


def chinese_tokenize(text: str) -> List[str]:
    """使用jieba进行中文分词"""
    import jieba
    # 英文单词作为整体
    words = jieba.cut(text)
    # 过滤停用词和短词
    stopwords = {'的', '是', '在', '和', '了', '有', '我', '你', '他', '她', '它', '们',
                 '这', '那', '个', '与', '或', '及', '等', '为', '以', '于', '也', '就',
                 '都', '而', '着', '一个', '没有', '我们', '你们', '可以', '进行', '使用'}
    return [w for w in words if w.strip() and len(w) > 1 and w not in stopwords]


def compute_tf(tokens: List[str]) -> Dict[str, float]:
    """计算词频TF"""
    tf = {}
    total = len(tokens) if tokens else 1
    for token in tokens:
        tf[token] = tf.get(token, 0) + 1
    for token in tf:
        tf[token] /= total
    return tf


def compute_idf(documents: List[List[str]]) -> Dict[str, float]:
    """计算逆文档频率IDF"""
    import math
    N = len(documents)
    idf = {}
    df = {}
    
    for doc in documents:
        for token in set(doc):
            df[token] = df.get(token, 0) + 1
    
    for token, freq in df.items():
        idf[token] = math.log((N + 1) / (freq + 1)) + 1
    
    return idf


def build_tfidf_vectors(texts: List[str]) -> np.ndarray:
    """构建TF-IDF向量矩阵"""
    global vocabulary, idf_values
    
    # 分词
    tokenized_docs = [chinese_tokenize(text) for text in texts]
    
    # 构建词表
    all_tokens = set()
    for doc in tokenized_docs:
        all_tokens.update(doc)
    
    vocabulary = {token: idx for idx, token in enumerate(sorted(all_tokens))}
    
    # 计算IDF
    idf_values = compute_idf(tokenized_docs)
    
    # 构建TF-IDF矩阵
    vectors = []
    for doc_tokens in tokenized_docs:
        tf = compute_tf(doc_tokens)
        vector = np.zeros(len(vocabulary))
        for token, tf_val in tf.items():
            if token in vocabulary:
                idx = vocabulary[token]
                idf_val = idf_values.get(token, 1.0)
                vector[idx] = tf_val * idf_val
        
        # L2归一化
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        vectors.append(vector)
    
    return np.array(vectors)


def get_text_embedding(text: str) -> List[float]:
    """获取单个文本的TF-IDF向量"""
    global vocabulary, idf_values
    
    tokens = chinese_tokenize(text)
    tf = compute_tf(tokens)
    
    vector = np.zeros(len(vocabulary)) if vocabulary else np.zeros(5000)
    
    for token in tokens:
        if token in vocabulary:
            idx = vocabulary[token]
            idf_val = idf_values.get(token, 1.0)
            vector[idx] = vector[idx] + tf.get(token, 0) * idf_val  # 累加词频
    
    # L2归一化
    norm = np.linalg.norm(vector)
    if norm > 0:
        vector = vector / norm
    
    return vector.tolist()


async def add_documents_tfidf(doc_ids: List[str], contents: List[str]) -> bool:
    """添加文档到TF-IDF索引"""
    global tfidf_matrix, doc_id_list, doc_contents
    
    # 追加新文档
    doc_id_list.extend(doc_ids)
    doc_contents.extend(contents)
    
    # 重新构建向量矩阵
    tfidf_matrix = build_tfidf_vectors(doc_contents)
    
    # 保存模型
    save_tfidf_model()
    
    print(f"TF-IDF索引更新: 共 {len(doc_contents)} 个文档")
    return True


async def search_tfidf(query: str, top_k: int = 10) -> List[Dict[str, Any]]:
    """TF-IDF语义搜索"""
    global tfidf_matrix, doc_id_list, doc_contents, vocabulary, idf_values
    
    if tfidf_matrix is None or len(doc_contents) == 0:
        return []
    
    # 对查询进行向量化
    query_tokens = chinese_tokenize(query)
    query_tf = compute_tf(query_tokens)
    
    query_vector = np.zeros(len(vocabulary))
    for token, tf_val in query_tf.items():
        if token in vocabulary:
            idx = vocabulary[token]
            idf_val = idf_values.get(token, 1.0)
            query_vector[idx] = tf_val * idf_val
    
    # L2归一化
    norm = np.linalg.norm(query_vector)
    if norm > 0:
        query_vector = query_vector / norm
    
    # 计算余弦相似度
    similarities = np.dot(tfidf_matrix, query_vector)
    
    # 获取top_k结果
    top_indices = np.argsort(similarities)[::-1][:top_k]
    
    results = []
    for idx in top_indices:
        if similarities[idx] > 0:
            results.append({
                "doc_id": doc_id_list[idx],
                "content": doc_contents[idx][:500],
                "score": float(similarities[idx]),
                "rank": len(results) + 1
            })
    
    return results


@router.post("/build")
async def build_tfidf_index(request: TFIDFEmbeddingRequest):
    """构建TF-IDF索引"""
    global tfidf_matrix, doc_id_list, doc_contents, vocabulary, idf_values
    
    start_time = datetime.now()
    
    # 构建向量
    doc_contents = request.texts
    doc_id_list = [f"doc_{i}" for i in range(len(request.texts))]
    
    tfidf_matrix = build_tfidf_vectors(request.texts)
    
    # 保存模型
    save_tfidf_model()
    
    processing_time = (datetime.now() - start_time).total_seconds()
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "document_count": len(request.texts),
            "vocabulary_size": len(vocabulary),
            "dimension": len(vocabulary),
            "processing_time": processing_time
        }
    }


@router.post("/search")
async def search_tfidf_index(request: TFIDFSearchRequest):
    """TF-IDF搜索"""
    results = await search_tfidf(request.query, request.top_k)
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "query": request.query,
            "results": results,
            "total": len(results)
        }
    }


@router.post("/encode")
async def encode_texts_tfidf(texts: List[str]):
    """文本向量化"""
    embeddings = [get_text_embedding(text) for text in texts]
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "embeddings": embeddings,
            "dimension": len(embeddings[0]) if embeddings else 0
        }
    }


@router.get("/stats")
async def get_tfidf_stats():
    """获取TF-IDF统计信息"""
    return {
        "code": 200,
        "message": "success",
        "data": {
            "document_count": len(doc_contents),
            "vocabulary_size": len(vocabulary),
            "dimension": len(vocabulary),
            "model_loaded": tfidf_matrix is not None
        }
    }


@router.post("/load")
async def load_tfidf():
    """加载保存的TF-IDF模型"""
    success = load_tfidf_model()
    
    return {
        "code": 200 if success else 404,
        "message": "模型加载成功" if success else "模型加载失败或不存在",
        "data": {
            "document_count": len(doc_contents),
            "vocabulary_size": len(vocabulary)
        }
    }


@router.post("/clear")
async def clear_tfidf_index():
    """清空TF-IDF索引"""
    global tfidf_matrix, doc_id_list, doc_contents, vocabulary, idf_values
    
    tfidf_matrix = None
    doc_id_list = []
    doc_contents = []
    vocabulary = {}
    idf_values = {}
    
    return {
        "code": 200,
        "message": "TF-IDF索引已清空"
    }


# 启动时尝试加载模型
load_tfidf_model()
