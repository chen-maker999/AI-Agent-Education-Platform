"""向量化嵌入服务 (EMBEDDING-SERVICE) - 真实sentence-transformers集成"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib
import json
import numpy as np
from common.core.config import settings

router = APIRouter(prefix="/embedding", tags=["Embedding Service"])

# 全局embedding模型
embedding_model = None
model_loaded = False

# 嵌入缓存
embedding_cache: Dict[str, List[float]] = {}


class EmbeddingRequest(BaseModel):
    """嵌入请求"""
    texts: List[str]
    batch_size: Optional[int] = None
    normalize: bool = True


class EmbeddingResponse(BaseModel):
    """嵌入响应"""
    embeddings: List[List[float]]
    model: str
    dimension: int
    batch_size: int
    processing_time: float


def load_embedding_model():
    """加载embedding模型"""
    global embedding_model, model_loaded
    
    if model_loaded:
        return True
    
    try:
        from sentence_transformers import SentenceTransformer
        embedding_model = SentenceTransformer(
            settings.EMBEDDING_MODEL,
            device=settings.EMBEDDING_DEVICE
        )
        model_loaded = True
        print(f"成功加载embedding模型: {settings.EMBEDDING_MODEL}")
        return True
    except ImportError:
        print("sentence-transformers未安装，使用模拟embedding")
        return False
    except Exception as e:
        print(f"加载embedding模型失败: {e}")
        return False


def get_embedding_cache_key(text: str) -> str:
    """获取embedding缓存key"""
    return hashlib.md5(text.encode()).hexdigest()


def get_cached_embedding(text: str) -> Optional[List[float]]:
    """从缓存获取embedding"""
    cache_key = get_embedding_cache_key(text)
    return embedding_cache.get(cache_key)


def cache_embedding(text: str, embedding: List[float]):
    """缓存embedding"""
    if len(embedding_cache) < 100000:  # 限制缓存大小
        cache_key = get_embedding_cache_key(text)
        embedding_cache[cache_key] = embedding


def generate_mock_embedding(text: str, dimension: int = 384) -> List[float]:
    """生成模拟embedding（当模型不可用时）"""
    # 使用文本的hash作为随机种子，保证相同文本生成相同向量
    hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
    np.random.seed(hash_val % (2**32))
    return np.random.randn(dimension).tolist()


async def generate_embeddings(
    texts: List[str], 
    batch_size: int = None,
    normalize: bool = True
) -> List[List[float]]:
    """
    生成文本嵌入向量
    
    Args:
        texts: 文本列表
        batch_size: 批处理大小
        normalize: 是否归一化
    
    Returns:
        嵌入向量列表
    """
    global embedding_model, model_loaded
    
    batch_size = batch_size or settings.EMBEDDING_BATCH_SIZE
    dimension = settings.EMBEDDING_DIMENSION
    
    # 尝试加载模型
    if not model_loaded:
        load_embedding_model()
    
    embeddings = []
    
    if model_loaded and embedding_model is not None:
        # 使用真实模型
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = embedding_model.encode(
                batch,
                normalize_embeddings=normalize,
                show_progress_bar=False
            )
            embeddings.extend(batch_embeddings.tolist())
    else:
        # 使用模拟embedding
        for text in texts:
            # 检查缓存
            cached = get_cached_embedding(text)
            if cached is not None:
                embeddings.append(cached)
            else:
                emb = generate_mock_embedding(text, dimension)
                if normalize:
                    emb = normalize_vector(emb)
                embeddings.append(emb)
                cache_embedding(text, emb)
    
    return embeddings


def normalize_vector(vec: List[float]) -> List[float]:
    """L2归一化"""
    arr = np.array(vec)
    norm = np.linalg.norm(arr)
    if norm > 0:
        arr = arr / norm
    return arr.tolist()


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """计算余弦相似度"""
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-8))


@router.post("/encode", response_model=EmbeddingResponse)
async def encode_texts(request: EmbeddingRequest):
    """
    批量生成文本嵌入
    
    使用 sentence-transformers/all-MiniLM-L6-v2 模型
    输出384维向量
    """
    start_time = datetime.now()
    
    # 生成embeddings
    embeddings = await generate_embeddings(
        request.texts,
        batch_size=request.batch_size,
        normalize=request.normalize
    )
    
    processing_time = (datetime.now() - start_time).total_seconds()
    
    return EmbeddingResponse(
        embeddings=embeddings,
        model=settings.EMBEDDING_MODEL if model_loaded else "mock",
        dimension=settings.EMBEDDING_DIMENSION,
        batch_size=request.batch_size or settings.EMBEDDING_BATCH_SIZE,
        processing_time=processing_time
    )


@router.post("/encode/single")
async def encode_single_text(text: str, normalize: bool = True):
    """单个文本嵌入"""
    embeddings = await generate_embeddings([text], normalize=normalize)
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "embedding": embeddings[0],
            "dimension": len(embeddings[0]),
            "cached": get_cached_embedding(text) is not None
        }
    }


@router.post("/similarity")
async def calculate_similarity(texts: List[str]):
    """计算文本间的相似度矩阵"""
    if len(texts) < 2:
        raise HTTPException(status_code=400, detail="需要至少2个文本")
    
    embeddings = await generate_embeddings(texts)
    
    # 计算相似度矩阵
    n = len(texts)
    similarity_matrix = np.zeros((n, n))
    
    for i in range(n):
        for j in range(n):
            similarity_matrix[i][j] = cosine_similarity(embeddings[i], embeddings[j])
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "texts": texts,
            "similarity_matrix": similarity_matrix.tolist(),
            "dimension": len(embeddings[0])
        }
    }


@router.get("/cache/stats")
async def get_cache_stats():
    """获取缓存统计"""
    return {
        "code": 200,
        "message": "success",
        "data": {
            "cache_size": len(embedding_cache),
            "max_size": 100000,
            "model_loaded": model_loaded,
            "model_name": settings.EMBEDDING_MODEL if model_loaded else None
        }
    }


@router.post("/cache/clear")
async def clear_cache():
    """清空缓存"""
    global embedding_cache
    embedding_cache.clear()
    return {
        "code": 200,
        "message": "缓存已清空",
        "data": {"cache_size": 0}
    }


@router.get("/model/info")
async def get_model_info():
    """获取模型信息"""
    return {
        "code": 200,
        "message": "success",
        "data": {
            "model_name": settings.EMBEDDING_MODEL,
            "dimension": settings.EMBEDDING_DIMENSION,
            "device": settings.EMBEDDING_DEVICE,
            "batch_size": settings.EMBEDDING_BATCH_SIZE,
            "loaded": model_loaded
        }
    }


# @router.on_event("startup")
# async def startup_event():
#     """启动时预热模型"""
#     load_embedding_model()
#     # 预热
#     if model_loaded:
#         await generate_embeddings(["warmup"])
