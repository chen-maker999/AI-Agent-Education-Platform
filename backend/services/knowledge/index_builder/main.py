"""离线索引构建器 - P0 修复：预计算文档向量，避免实时计算"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import hashlib
import pickle
import os
import json
import numpy as np
from sqlalchemy import select, text
import aiofiles

router = APIRouter(prefix="/index-builder", tags=["Offline Index Builder"])

# ==================== 数据模型 ====================
class IndexBuildRequest(BaseModel):
    """索引构建请求"""
    course_id: Optional[str] = None
    batch_size: int = 100
    rebuild_all: bool = False


class IndexBuildResponse(BaseModel):
    """索引构建响应"""
    total_docs: int
    indexed_docs: int
    faiss_vectors: int
    tfidf_vectors: int
    build_time: float
    status: str


class IndexStats(BaseModel):
    """索引统计信息"""
    total_docs: int
    faiss_index_docs: int
    tfidf_index_docs: int
    last_build_time: Optional[str]
    index_status: str


# ==================== 全局状态 ====================
_index_stats = {
    "total_docs": 0,
    "faiss_index_docs": 0,
    "tfidf_index_docs": 0,
    "last_build_time": None,
    "index_status": "not_built"  # not_built, building, ready, error
}

# 文档向量缓存 (用于快速查询)
_doc_vector_cache: Dict[str, np.ndarray] = {}
_doc_cache_path = "data/doc_vector_cache.pkl"


# ==================== 结构化日志 ====================
import logging
import uuid as uuid_module

logger = logging.getLogger("index_builder")


def get_structured_logger(request_id: Optional[str] = None):
    """获取结构化日志器"""
    extra = {
        "request_id": request_id or str(uuid_module.uuid4()),
        "service": "index_builder"
    }
    return logging.LoggerAdapter(logger, extra)


class StructuredFormatter(logging.Formatter):
    """JSON 格式化器"""
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "request_id": getattr(record, 'request_id', 'N/A'),
            "service": getattr(record, 'service', 'index_builder'),
        }
        if hasattr(record, 'exc_info') and record.exc_info:
            import traceback
            log_data["traceback"] = traceback.format_exception(*record.exc_info)
        return json.dumps(log_data, ensure_ascii=False)


# 配置日志
logging.basicConfig(level=logging.INFO)
for handler in logging.getLogger().handlers:
    handler.setFormatter(StructuredFormatter())


# ==================== 向量计算 ====================
def compute_tfidf_vector(text: str, vocabulary: Dict[str, int], idf_values: Dict[str, float]) -> np.ndarray:
    """计算 TF-IDF 向量 (O(1) 复杂度，使用预计算的 IDF)"""
    from services.knowledge.embedding.tfidf_main import chinese_tokenize, compute_tf

    tokens = chinese_tokenize(text)
    tf = compute_tf(tokens)

    vector_dim = len(vocabulary) if vocabulary else 5000
    vector = np.zeros(vector_dim)

    for token, tf_val in tf.items():
        if token in vocabulary:
            idx = vocabulary[token]
            idf_val = idf_values.get(token, 1.0)
            vector[idx] = tf_val * idf_val

    # L2 归一化
    norm = np.linalg.norm(vector)
    if norm > 0:
        vector = vector / norm

    return vector


async def compute_embedding_batch(contents: List[str]) -> List[List[float]]:
    """批量计算嵌入向量"""
    # 使用 TF-IDF 本地嵌入
    from services.knowledge.embedding.tfidf_main import get_text_embedding

    # 批量计算嵌入
    embeddings = []
    for content in contents:
        try:
            embedding = get_text_embedding(content)
            embeddings.append(embedding)
        except Exception as e:
            logger.error(f"嵌入计算失败：{e}")
            embeddings.append([0.0] * 5000)  # 返回零向量 (TF-IDF 默认维度)

    return embeddings


# ==================== 索引构建 ====================
async def build_faiss_index_from_db(course_id: Optional[str] = None) -> int:
    """从数据库构建 FAISS 索引（使用 TF-IDF 嵌入，不依赖外部模型）"""
    from common.database.postgresql import AsyncSessionLocal
    from services.knowledge.rag.main import RAGDocument
    from services.knowledge.faiss_indexer.main import (
        faiss_index, index_metadata, doc_id_to_index, index_to_doc_id,
        initialize_faiss_index, add_vectors_to_index
    )
    from services.knowledge.embedding.tfidf_main import get_text_embedding

    indexed_count = 0
    request_id = str(uuid_module.uuid4())
    log = get_structured_logger(request_id)

    log.info("开始构建 FAISS 索引（使用 TF-IDF 嵌入）")

    # 初始化 FAISS 索引
    if faiss_index is None:
        initialize_faiss_index(use_hnsw=True)

    async with AsyncSessionLocal() as session:
        # 分页查询文档
        offset = 0
        batch_size = 100

        while True:
            if course_id:
                result = await session.execute(
                    select(RAGDocument.doc_id, RAGDocument.content)
                    .where(RAGDocument.course_id == course_id)
                    .offset(offset)
                    .limit(batch_size)
                )
            else:
                result = await session.execute(
                    select(RAGDocument.doc_id, RAGDocument.content)
                    .offset(offset)
                    .limit(batch_size)
                )

            rows = result.all()
            if not rows:
                break

            doc_ids = [row.doc_id for row in rows]
            contents = [row.content for row in rows]

            # 使用 TF-IDF 计算嵌入向量（不依赖外部模型）
            embeddings = []
            for content in contents:
                try:
                    embedding = get_text_embedding(content)
                    embeddings.append(embedding)
                except Exception as e:
                    log.error(f"TF-IDF 嵌入计算失败：{e}")
                    embeddings.append([0.0] * 5000)  # 返回零向量

            vectors = np.array(embeddings).astype('float32')

            # 添加到 FAISS 索引
            add_vectors_to_index(vectors, doc_ids)
            indexed_count += len(doc_ids)

            offset += batch_size
            log.info(f"已处理 {indexed_count} 个文档")

    log.info(f"FAISS 索引构建完成：{indexed_count} 个文档（使用 TF-IDF 嵌入）")
    return indexed_count


async def build_tfidf_index_from_db(course_id: Optional[str] = None) -> int:
    """从数据库构建 TF-IDF 索引 (离线预计算版本，P11 优化：集成语义分块)"""
    from common.database.postgresql import AsyncSessionLocal
    from services.knowledge.rag.main import RAGDocument
    from services.knowledge.embedding.tfidf_main import (
        chinese_tokenize, compute_idf, build_tfidf_vectors,
        tfidf_matrix, doc_id_list, doc_contents, vocabulary, idf_values
    )
    # P11 新增：导入语义分块
    from services.knowledge.chunk.semantic_chunking import semantic_chunking as semantic_chunking_func

    request_id = str(uuid_module.uuid4())
    log = get_structured_logger(request_id)

    log.info("开始构建 TF-IDF 索引（使用语义分块）")

    # 从数据库查询所有文档
    async with AsyncSessionLocal() as session:
        if course_id:
            result = await session.execute(
                select(RAGDocument.doc_id, RAGDocument.content)
                .where(RAGDocument.course_id == course_id)
            )
        else:
            result = await session.execute(
                select(RAGDocument.doc_id, RAGDocument.content)
            )

        rows = result.all()

    if not rows:
        log.warning("未找到文档")
        return 0

    # P11 优化：使用语义分块处理文档内容
    doc_ids = []
    contents = []
    total_chunks = 0
    
    log.info(f"查询到 {len(rows)} 个文档，开始语义分块处理")
    
    for row in rows:
        doc_id = row.doc_id
        content = row.content
        
        # 使用语义分块
        chunks = semantic_chunking_func(
            text=content,
            max_chunk_size=1500,
            min_chunk_size=200,
            overlap_ratio=0.15,
            use_semantic_boundary=True
        )
        
        if chunks:
            for chunk in chunks:
                chunk_id = f"{doc_id}_{chunk['chunk_id']}"
                doc_ids.append(chunk_id)
                contents.append(chunk["content"])
            total_chunks += len(chunks)
        else:
            # 如果分块失败，使用原文档
            doc_ids.append(doc_id)
            contents.append(content)
            total_chunks += 1
    
    log.info(f"语义分块完成：{len(rows)} 个文档 → {total_chunks} 个块")

    # 构建 TF-IDF 向量矩阵 (一次性构建，避免实时计算)
    vectors = build_tfidf_vectors(contents)

    # 更新全局状态
    from services.knowledge.embedding import tfidf_main
    tfidf_main.tfidf_matrix = vectors
    tfidf_main.doc_id_list = doc_ids
    tfidf_main.doc_contents = contents

    # 保存到缓存
    await save_vector_cache()

    # 保存 TF-IDF 模型
    from services.knowledge.embedding.tfidf_main import save_tfidf_model
    save_tfidf_model()

    log.info(f"TF-IDF 索引构建完成：{total_chunks} 个块（来自 {len(rows)} 个文档）")
    return total_chunks


async def save_vector_cache():
    """保存文档向量缓存到磁盘"""
    from services.knowledge.embedding.tfidf_main import (
        tfidf_matrix, doc_id_list, vocabulary, idf_values
    )

    os.makedirs(os.path.dirname(_doc_cache_path), exist_ok=True)

    try:
        async with aiofiles.open(_doc_cache_path, 'wb') as f:
            cache_data = {
                "tfidf_matrix": tfidf_matrix,
                "doc_id_list": doc_id_list,
                "vocabulary": vocabulary,
                "idf_values": idf_values,
                "timestamp": datetime.utcnow().isoformat()
            }
            await f.write(pickle.dumps(cache_data))
        logger.info(f"向量缓存已保存：{_doc_cache_path}")
    except Exception as e:
        logger.error(f"保存向量缓存失败：{e}")


async def load_vector_cache() -> bool:
    """从磁盘加载文档向量缓存"""
    global _doc_vector_cache

    if not os.path.exists(_doc_cache_path):
        return False

    try:
        async with aiofiles.open(_doc_cache_path, 'rb') as f:
            content = await f.read()
            cache_data = pickle.loads(content)

            # 更新 TF-IDF 模块的全局状态
            from services.knowledge.embedding import tfidf_main
            tfidf_main.tfidf_matrix = cache_data.get("tfidf_matrix")
            tfidf_main.doc_id_list = cache_data.get("doc_id_list", [])
            tfidf_main.vocabulary = cache_data.get("vocabulary", {})
            tfidf_main.idf_values = cache_data.get("idf_values", {})

            logger.info(f"向量缓存已加载：{len(cache_data.get('doc_id_list', []))} 个文档")
            return True
    except Exception as e:
        logger.error(f"加载向量缓存失败：{e}")
        return False


# ==================== API 接口 ====================
@router.post("/build")
async def build_all_indices(request: IndexBuildRequest):
    """构建所有索引 (FAISS + TF-IDF)"""
    global _index_stats

    request_id = str(uuid_module.uuid4())
    log = get_structured_logger(request_id)

    start_time = datetime.now()
    _index_stats["index_status"] = "building"

    try:
        # 构建 TF-IDF 索引
        log.info("开始构建 TF-IDF 索引")
        tfidf_count = await build_tfidf_index_from_db(request.course_id)

        # 构建 FAISS 索引
        log.info("开始构建 FAISS 索引")
        faiss_count = await build_faiss_index_from_db(request.course_id)

        build_time = (datetime.now() - start_time).total_seconds()

        _index_stats.update({
            "total_docs": max(tfidf_count, faiss_count),
            "faiss_index_docs": faiss_count,
            "tfidf_index_docs": tfidf_count,
            "last_build_time": datetime.utcnow().isoformat(),
            "index_status": "ready"
        })

        log.info(f"索引构建完成：TF-IDF={tfidf_count}, FAISS={faiss_count}, 耗时={build_time:.2f}s")

        return IndexBuildResponse(
            total_docs=max(tfidf_count, faiss_count),
            indexed_docs=max(tfidf_count, faiss_count),
            faiss_vectors=faiss_count,
            tfidf_vectors=tfidf_count,
            build_time=build_time,
            status="success"
        )

    except Exception as e:
        _index_stats["index_status"] = "error"
        log.error(f"索引构建失败：{e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"索引构建失败：{str(e)}")


@router.post("/build/background")
async def build_indices_background(request: IndexBuildRequest, background_tasks: BackgroundTasks):
    """后台构建索引 (不阻塞请求)"""
    background_tasks.add_task(build_all_indices, request)

    return {
        "code": 200,
        "message": "索引构建任务已启动，将在后台执行"
    }


@router.get("/stats")
async def get_index_stats():
    """获取索引统计信息"""
    return {
        "code": 200,
        "message": "success",
        "data": _index_stats
    }


@router.post("/cache/save")
async def save_cache():
    """保存向量缓存"""
    await save_vector_cache()
    return {"code": 200, "message": "缓存保存成功"}


@router.post("/cache/load")
async def load_cache():
    """加载向量缓存"""
    success = await load_vector_cache()
    return {
        "code": 200 if success else 404,
        "message": "缓存加载成功" if success else "缓存不存在或加载失败"
    }


@router.delete("/cache/clear")
async def clear_cache():
    """清除向量缓存"""
    global _doc_vector_cache

    if os.path.exists(_doc_cache_path):
        os.remove(_doc_cache_path)

    _doc_vector_cache = {}

    return {"code": 200, "message": "缓存已清除"}


@router.on_event("startup")
async def startup_load_cache():
    """启动时自动加载缓存"""
    await load_vector_cache()
