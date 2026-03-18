"""FAISS索引构建 (FAISS-INDEXER) - IVF+PQ优化索引"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib
import json
import numpy as np
import pickle
import os
from common.core.config import settings

router = APIRouter(prefix="/faiss", tags=["FAISS Indexer"])


@router.get("/", response_model=dict)
async def get_faiss_stats():
    """获取FAISS索引状态"""
    return {"code": 200, "message": "success", "data": {"status": "ok", "service": "faiss indexer"}}


@router.get("/stats", response_model=dict)
async def get_faiss_stats_alias():
    """获取FAISS索引统计信息"""
    return {
        "code": 200,
        "message": "success",
        "data": {
            "total_vectors": index_metadata.get("total_vectors", 0),
            "dimension": index_metadata.get("dimension", settings.FAISS_DIMENSION),
            "index_type": index_metadata.get("index_type", settings.FAISS_INDEX_TYPE),
            "created_at": index_metadata.get("created_at"),
            "last_updated": index_metadata.get("last_updated"),
            "service": "faiss"
        }
    }


# 全局FAISS索引
faiss_index = None
index_metadata: Dict[str, Any] = {
    "total_vectors": 0,
    "dimension": settings.FAISS_DIMENSION,
    "index_type": settings.FAISS_INDEX_TYPE,
    "created_at": None,
    "last_updated": None
}

# 文档映射
doc_id_to_index: Dict[str, int] = {}
index_to_doc_id: Dict[int, str] = {}


class IndexDocument(BaseModel):
    """索引文档"""
    doc_id: str
    content: str
    metadata: Dict[str, Any] = {}


class IndexRequest(BaseModel):
    """索引请求"""
    documents: List[IndexDocument]
    batch_size: int = 64


class SearchRequest(BaseModel):
    """搜索请求"""
    query: str
    query_embedding: Optional[List[float]] = None
    top_k: int = 10
    nprobe: int = settings.FAISS_NPROBE
    filters: Optional[Dict[str, Any]] = None


def initialize_faiss_index():
    """初始化FAISS索引"""
    global faiss_index, index_metadata
    
    dimension = settings.FAISS_DIMENSION
    index_type = settings.FAISS_INDEX_TYPE
    
    try:
        import faiss
        
        if "IVF" in index_type and "PQ" in index_type:
            # IVF+PQ 索引 - 适合大数据集
            nlist = settings.FAISS_NLIST  # 聚类数量
            m = 16  # PQ子空间数
            nbits = 8  # 每个子空间的位数
            
            # 先创建量化器
            quantizer = faiss.IndexFlatL2(dimension)
            # 创建IVF-PQ索引
            faiss_index = faiss.IndexIVFPQ(quantizer, dimension, nlist, m, nbits)
        elif "IVF" in index_type:
            # 纯IVF索引
            nlist = settings.FAISS_NLIST
            quantizer = faiss.IndexFlatL2(dimension)
            faiss_index = faiss.IndexIVF(quantizer, dimension, nlist)
        else:
            # 平面索引 - 适合小数据集，精确搜索
            faiss_index = faiss.IndexFlatL2(dimension)
        
        index_metadata["created_at"] = datetime.utcnow().isoformat()
        print(f"FAISS索引初始化成功: {index_type}, dimension={dimension}")
        return True
        
    except ImportError:
        print("FAISS未安装")
        return False
    except Exception as e:
        print(f"FAISS索引初始化失败: {e}")
        return False


def add_vectors_to_index(vectors: np.ndarray, doc_ids: List[str]):
    """添加向量到索引"""
    global faiss_index, index_metadata, doc_id_to_index, index_to_doc_id
    
    if faiss_index is None:
        initialize_faiss_index()
    
    if faiss_index is None:
        return
    
    # 如果是IVF索引，需要先训练
    if hasattr(faiss_index, 'is_trained') and not faiss_index.is_trained:
        # 训练索引
        train_vectors = vectors[:min(len(vectors), 10000)]
        faiss_index.train(train_vectors)
    
    # 添加向量
    faiss_index.add(vectors)
    
    # 更新映射
    start_idx = faiss_index.ntotal - len(vectors)
    for i, doc_id in enumerate(doc_ids):
        doc_id_to_index[doc_id] = start_idx + i
        index_to_doc_id[start_idx + i] = doc_id
    
    index_metadata["total_vectors"] = faiss_index.ntotal
    index_metadata["last_updated"] = datetime.utcnow().isoformat()


async def search_vectors(
    query_embedding: np.ndarray,
    top_k: int = 10,
    nprobe: int = settings.FAISS_NPROBE
) -> List[Dict[str, Any]]:
    """搜索向量"""
    global faiss_index, index_metadata, index_to_doc_id
    
    if faiss_index is None or faiss_index.ntotal == 0:
        return []
    
    # 设置搜索参数
    if hasattr(faiss_index, 'nprobe'):
        faiss_index.nprobe = nprobe
    
    # 搜索
    query_embedding = query_embedding.reshape(1, -1).astype('float32')
    distances, indices = faiss_index.search(query_embedding, min(top_k, faiss_index.ntotal))
    
    # 构建结果
    results = []
    for i, idx in enumerate(indices[0]):
        if idx >= 0 and idx in index_to_doc_id:
            doc_id = index_to_doc_id[idx]
            # 将距离转换为相似度分数
            score = float(1 / (1 + distances[0][i]))
            results.append({
                "doc_id": doc_id,
                "distance": float(distances[0][i]),
                "score": score,
                "rank": i + 1
            })
    
    return results


def save_index_to_disk(path: str = "faiss_index.bin"):
    """保存索引到磁盘"""
    global faiss_index, index_metadata, doc_id_to_index
    
    if faiss_index is None:
        return False
    
    try:
        import faiss
        
        # 保存FAISS索引
        faiss.write_index(faiss_index, path)
        
        # 保存元数据和映射
        metadata = {
            "index_metadata": index_metadata,
            "doc_id_to_index": doc_id_to_index,
            "index_to_doc_id": index_to_doc_id
        }
        
        with open(f"{path}.meta", "wb") as f:
            pickle.dump(metadata, f)
        
        return True
    except Exception as e:
        print(f"保存索引失败: {e}")
        return False


def load_index_from_disk(path: str = "faiss_index.bin"):
    """从磁盘加载索引"""
    global faiss_index, index_metadata, doc_id_to_index, index_to_doc_id
    
    try:
        import faiss
        
        if not os.path.exists(path):
            return False
        
        # 加载FAISS索引
        faiss_index = faiss.read_index(path)
        
        # 加载元数据
        meta_path = f"{path}.meta"
        if os.path.exists(meta_path):
            with open(meta_path, "rb") as f:
                metadata = pickle.load(f)
                index_metadata = metadata.get("index_metadata", index_metadata)
                doc_id_to_index = metadata.get("doc_id_to_index", {})
                index_to_doc_id = metadata.get("index_to_doc_id", {})
        
        print(f"索引加载成功: {faiss_index.ntotal} vectors")
        return True
    except Exception as e:
        print(f"加载索引失败: {e}")
        return False


@router.post("/build", status_code=201)
async def build_index(request: IndexRequest, background_tasks: BackgroundTasks):
    """构建FAISS索引"""
    from services.knowledge.embedding.main import generate_embeddings
    
    global faiss_index
    
    # 初始化索引
    if faiss_index is None:
        initialize_faiss_index()
    
    # 提取文本内容
    contents = [doc.content for doc in request.documents]
    doc_ids = [doc.doc_id for doc in request.documents]
    
    # 生成embeddings
    embeddings = await generate_embeddings(contents)
    
    # 转换为numpy数组
    vectors = np.array(embeddings).astype('float32')
    
    # 添加到索引
    add_vectors_to_index(vectors, doc_ids)
    
    return {
        "code": 201,
        "message": f"成功添加 {len(contents)} 个向量到索引",
        "data": {
            "indexed_count": len(contents),
            "total_vectors": index_metadata["total_vectors"],
            "dimension": index_metadata["dimension"]
        }
    }


@router.post("/search")
async def search_index(request: SearchRequest):
    """向量语义搜索"""
    from services.knowledge.embedding.main import generate_embeddings
    
    # 获取查询向量
    if request.query_embedding:
        query_embedding = np.array(request.query_embedding).astype('float32')
    else:
        embeddings = await generate_embeddings([request.query])
        query_embedding = np.array(embeddings[0]).astype('float32')
    
    # 搜索
    results = await search_vectors(
        query_embedding,
        top_k=request.top_k,
        nprobe=request.nprobe
    )
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "query": request.query,
            "results": results,
            "total": len(results),
            "search_method": "faiss"
        }
    }


@router.post("/save")
async def save_index(path: str = "faiss_index.bin"):
    """保存索引到磁盘"""
    success = save_index_to_disk(path)
    
    return {
        "code": 200 if success else 500,
        "message": "索引保存成功" if success else "索引保存失败",
        "data": {"path": path}
    }


@router.post("/load")
async def load_index(path: str = "faiss_index.bin"):
    """从磁盘加载索引"""
    success = load_index_from_disk(path)
    
    return {
        "code": 200 if success else 404,
        "message": "索引加载成功" if success else "索引加载失败",
        "data": {
            "path": path,
            "total_vectors": index_metadata["total_vectors"]
        }
    }


@router.get("/status")
async def get_index_status():
    """获取索引状态"""
    return {
        "code": 200,
        "message": "success",
        "data": {
            "initialized": faiss_index is not None,
            "metadata": index_metadata
        }
    }


@router.delete("/reset")
async def reset_index():
    """重置索引"""
    global faiss_index, index_metadata, doc_id_to_index, index_to_doc_id
    
    faiss_index = None
    index_metadata = {
        "total_vectors": 0,
        "dimension": settings.FAISS_DIMENSION,
        "index_type": settings.FAISS_INDEX_TYPE,
        "created_at": None,
        "last_updated": None
    }
    doc_id_to_index = {}
    index_to_doc_id = {}
    
    return {
        "code": 200,
        "message": "索引已重置",
        "data": {"total_vectors": 0}
    }


# @router.on_event("startup")
# async def startup_event():
#     """启动时初始化索引"""
#     initialize_faiss_index()
