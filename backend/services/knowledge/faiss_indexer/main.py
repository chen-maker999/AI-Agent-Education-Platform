"""FAISS 索引构建 (FAISS-INDEXER) - 支持 IVF+PQ 和 HNSW 索引优化"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np
import pickle
import os
import faiss
from common.core.config import settings

router = APIRouter(prefix="/faiss", tags=["FAISS Indexer"])

# ==================== HNSW 配置 - P11 优化：提升检索质量 ====================
class HNSWConfig:
    """HNSW 索引配置 - P11 优化参数"""
    M = 32  # 最大邻居数 (保持不变)
    EF_CONSTRUCTION = 256  # P11 优化：从 200 提升至 256，提高构建质量
    EF_SEARCH = 100  # P11 优化：从 64 提升至 100，提高检索精度


# ==================== 数据模型 ====================
class IndexDocument(BaseModel):
    """索引文档"""
    doc_id: str
    content: str
    metadata: Dict[str, Any] = {}


class IndexRequest(BaseModel):
    """索引请求"""
    documents: List[IndexDocument]
    batch_size: int = 64
    use_hnsw: bool = True  # 是否使用 HNSW 索引


class SearchRequest(BaseModel):
    """搜索请求"""
    query: str
    query_embedding: Optional[List[float]] = None
    top_k: int = 10
    nprobe: int = settings.FAISS_NPROBE
    ef_search: int = HNSWConfig.EF_SEARCH
    filters: Optional[Dict[str, Any]] = None


# ==================== 全局索引 ====================
faiss_index = None
index_metadata: Dict[str, Any] = {
    "total_vectors": 0,
    "dimension": settings.FAISS_DIMENSION,
    "index_type": "HNSW",  # 默认使用 HNSW
    "created_at": None,
    "last_updated": None,
    "hnsw_config": {
        "M": HNSWConfig.M,
        "ef_construction": HNSWConfig.EF_CONSTRUCTION,
        "ef_search": HNSWConfig.EF_SEARCH
    }
}

# 文档映射
doc_id_to_index: Dict[str, int] = {}
index_to_doc_id: Dict[int, str] = {}


# ==================== 索引初始化 ====================
def initialize_faiss_index(use_hnsw: bool = True):
    """
    初始化 FAISS 索引
    
    支持两种索引类型:
    1. HNSW: 适合实时检索，速度快，精度高
    2. IVF+PQ: 适合大数据集，内存占用小
    """
    global faiss_index, index_metadata

    dimension = settings.FAISS_DIMENSION

    try:
        import faiss

        if use_hnsw:
            # ========== HNSW 索引 (推荐) ==========
            # HNSW (Hierarchical Navigable Small World)
            # 优势:
            # - 检索速度极快 (微秒级)
            # - 召回率高
            # - 无需训练
            # 劣势:
            # - 内存占用较大
            # - 构建时间较长
            
            faiss_index = faiss.IndexHNSWFlat(
                dimension, 
                HNSWConfig.M,
                faiss.METRIC_INNER_PRODUCT  # 使用内积相似度
            )
            faiss_index.hnsw.efConstruction = HNSWConfig.EF_CONSTRUCTION
            faiss_index.hnsw.efSearch = HNSWConfig.EF_SEARCH
            
            index_metadata["index_type"] = "HNSW"
            index_metadata["hnsw_config"] = {
                "M": HNSWConfig.M,
                "ef_construction": HNSWConfig.EF_CONSTRUCTION,
                "ef_search": HNSWConfig.EF_SEARCH
            }
            
            print(f"FAISS HNSW 索引初始化成功：M={HNSWConfig.M}, ef_construction={HNSWConfig.EF_CONSTRUCTION}")
            
        else:
            # ========== IVF+PQ 索引 ==========
            # 适合大数据集 (>100 万向量)
            nlist = settings.FAISS_NLIST
            m = 16  # PQ 子空间数
            nbits = 8
            
            quantizer = faiss.IndexFlatIP(dimension)  # 使用内积
            faiss_index = faiss.IndexIVFPQ(quantizer, dimension, nlist, m, nbits)
            
            index_metadata["index_type"] = "IVF-PQ"
            index_metadata["ivf_config"] = {
                "nlist": nlist,
                "m": m,
                "nbits": nbits
            }
            
            print(f"FAISS IVF-PQ 索引初始化成功：nlist={nlist}, m={m}")

        index_metadata["created_at"] = datetime.utcnow().isoformat()
        return True

    except ImportError:
        print("FAISS 未安装，请运行：pip install faiss-cpu")
        return False
    except Exception as e:
        print(f"FAISS 索引初始化失败：{e}")
        return False


# ==================== 索引操作 ====================
def add_vectors_to_index(vectors: np.ndarray, doc_ids: List[str]):
    """添加向量到索引"""
    global faiss_index, index_metadata, doc_id_to_index, index_to_doc_id

    if faiss_index is None:
        initialize_faiss_index()

    if faiss_index is None:
        return

    # 归一化向量 (对于内积相似度很重要)
    if index_metadata["index_type"] == "HNSW":
        faiss.normalize_L2(vectors)
    
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
    nprobe: int = 20,  # P11 优化：从 FAISS_NPROBE 提升至 20，增加搜索范围
    ef_search: int = HNSWConfig.EF_SEARCH
) -> List[Dict[str, Any]]:
    """搜索向量 - P11 优化：默认增加搜索深度提升召回率"""
    global faiss_index, index_metadata, index_to_doc_id

    if faiss_index is None or faiss_index.ntotal == 0:
        return []

    # 设置搜索参数
    if index_metadata["index_type"] == "HNSW":
        # HNSW 使用 efSearch 参数
        faiss_index.hnsw.efSearch = ef_search
        # 归一化查询向量
        query_embedding = query_embedding.reshape(1, -1).astype('float32')
        faiss.normalize_L2(query_embedding)
    else:
        # IVF 使用 nprobe 参数
        if hasattr(faiss_index, 'nprobe'):
            faiss_index.nprobe = nprobe
        query_embedding = query_embedding.reshape(1, -1).astype('float32')

    # 搜索
    distances, indices = faiss_index.search(query_embedding, min(top_k, faiss_index.ntotal))

    # 构建结果
    results = []
    for i, idx in enumerate(indices[0]):
        if idx >= 0 and idx in index_to_doc_id:
            doc_id = index_to_doc_id[idx]
            # 将距离转换为相似度分数 (0-1 范围)
            score = float(1 / (1 + distances[0][i])) if distances[0][i] >= 0 else float(distances[0][i])
            results.append({
                "doc_id": doc_id,
                "distance": float(distances[0][i]),
                "score": score,
                "rank": i + 1
            })

    return results


# ==================== 持久化 ====================
INDEX_SAVE_PATH = "data/faiss_index.bin"
INDEX_META_PATH = "data/faiss_index.meta.pkl"
INDEX_BACKUP_PATH = "data/faiss_index.bin.backup"
MAX_BACKUPS = 3  # 保留最近 3 个备份


def save_index_to_disk(path: str = None, create_backup: bool = True):
    """
    保存索引到磁盘 (原子操作 + 备份) - BACKEND-005 修复
    
    Args:
        path: 保存路径
        create_backup: 是否创建备份
        
    Returns:
        是否成功
    """
    global faiss_index, index_metadata, doc_id_to_index

    if faiss_index is None:
        print("FAISS 索引未初始化，无法保存")
        return False

    if path is None:
        path = INDEX_SAVE_PATH

    try:
        import faiss
        import shutil

        # 确保目录存在
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)

        # 1. 创建备份 (如果存在旧索引)
        if create_backup and os.path.exists(path):
            try:
                # 轮转备份文件
                for i in range(MAX_BACKUPS, 0, -1):
                    old_backup = f"{path}.backup.{i}"
                    new_backup = f"{path}.backup.{i + 1}"
                    if os.path.exists(old_backup):
                        if i == MAX_BACKUPS:
                            os.remove(old_backup)  # 删除最旧的备份
                        else:
                            shutil.copy2(old_backup, new_backup)
                
                # 移动当前备份
                backup_path = f"{path}.backup.1"
                shutil.copy2(path, backup_path)
                shutil.copy2(f"{path}.meta.pkl", f"{backup_path}.meta.pkl")
                print(f"已创建备份：{backup_path}")
            except Exception as e:
                print(f"创建备份失败：{e}")

        # 2. 写入临时文件 (原子操作第一步)
        temp_path = f"{path}.tmp"
        temp_meta_path = f"{path}.tmp.meta.pkl"
        
        try:
            faiss.write_index(faiss_index, temp_path)
            
            # 保存元数据到临时文件
            metadata = {
                "index_metadata": index_metadata,
                "doc_id_to_index": doc_id_to_index,
                "index_to_doc_id": index_to_doc_id
            }
            with open(temp_meta_path, "wb") as f:
                pickle.dump(metadata, f)
        except Exception as e:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)
            if os.path.exists(temp_meta_path):
                os.remove(temp_meta_path)
            raise e

        # 3. 原子替换 (先删后移)
        if os.path.exists(path):
            os.remove(path)
        if os.path.exists(f"{path}.meta.pkl"):
            os.remove(f"{path}.meta.pkl")
        
        shutil.move(temp_path, path)
        shutil.move(temp_meta_path, f"{path}.meta.pkl")

        print(f"FAISS 索引保存到磁盘 (原子操作): {path} ({faiss_index.ntotal} vectors)")
        return True

    except Exception as e:
        print(f"保存索引失败：{e}")
        return False


def load_index_from_disk(path: str = None, try_backup: bool = True):
    """
    从磁盘加载索引 (支持备份恢复) - BACKEND-005 修复
    
    Args:
        path: 加载路径
        try_backup: 加载失败时是否尝试备份
        
    Returns:
        是否成功
    """
    global faiss_index, index_metadata, doc_id_to_index, index_to_doc_id

    if path is None:
        path = INDEX_SAVE_PATH

    try:
        import faiss

        if not os.path.exists(path):
            print(f"FAISS 索引文件不存在：{path}")
            if try_backup:
                # 尝试从备份恢复
                backup_path = f"{path}.backup.1"
                if os.path.exists(backup_path):
                    print(f"尝试从备份恢复：{backup_path}")
                    return load_index_from_disk(backup_path, try_backup=False)
            return False

        # 加载 FAISS 索引
        faiss_index = faiss.read_index(path)

        # 加载元数据
        meta_path = f"{path}.meta.pkl"
        if os.path.exists(meta_path):
            with open(meta_path, "rb") as f:
                metadata = pickle.load(f)
                index_metadata.update(metadata.get("index_metadata", {}))
                doc_id_to_index.update(metadata.get("doc_id_to_index", {}))
                index_to_doc_id.update(metadata.get("index_to_doc_id", {}))

        print(f"FAISS 索引加载成功：{faiss_index.ntotal} vectors")
        return True
        
    except Exception as e:
        print(f"加载索引失败：{e}")
        if try_backup:
            # 尝试从备份恢复
            backup_path = f"{path}.backup.1"
            if os.path.exists(backup_path):
                print(f"尝试从备份恢复：{backup_path}")
                return load_index_from_disk(backup_path, try_backup=False)
        return False


# ==================== API 接口 ====================
@router.get("/", response_model=dict)
async def get_faiss_stats():
    """获取 FAISS 索引状态"""
    return {
        "code": 200,
        "message": "success",
        "data": {
            "status": "ok",
            "service": "faiss indexer",
            "index_type": index_metadata.get("index_type", "HNSW"),
            "total_vectors": index_metadata.get("total_vectors", 0)
        }
    }


@router.get("/stats", response_model=dict)
async def get_faiss_stats_detail():
    """获取 FAISS 索引详细统计信息"""
    return {
        "code": 200,
        "message": "success",
        "data": {
            "total_vectors": index_metadata.get("total_vectors", 0),
            "dimension": index_metadata.get("dimension", settings.FAISS_DIMENSION),
            "index_type": index_metadata.get("index_type", "HNSW"),
            "created_at": index_metadata.get("created_at"),
            "last_updated": index_metadata.get("last_updated"),
            "hnsw_config": index_metadata.get("hnsw_config"),
            "ivf_config": index_metadata.get("ivf_config"),
            "service": "faiss"
        }
    }


@router.post("/build", status_code=201)
async def build_index(request: IndexRequest, background_tasks: BackgroundTasks):
    """构建 FAISS 索引"""
    from services.knowledge.embedding.main import generate_embeddings

    global faiss_index

    # 初始化索引
    if faiss_index is None:
        initialize_faiss_index(use_hnsw=request.use_hnsw)

    # 提取文本内容
    contents = [doc.content for doc in request.documents]
    doc_ids = [doc.doc_id for doc in request.documents]

    # 生成 embeddings
    embeddings = await generate_embeddings(contents)

    # 转换为 numpy 数组
    vectors = np.array(embeddings).astype('float32')

    # 添加到索引
    add_vectors_to_index(vectors, doc_ids)

    return {
        "code": 201,
        "message": f"成功添加 {len(contents)} 个向量到索引",
        "data": {
            "indexed_count": len(contents),
            "total_vectors": index_metadata["total_vectors"],
            "dimension": index_metadata["dimension"],
            "index_type": index_metadata["index_type"]
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
        nprobe=request.nprobe,
        ef_search=request.ef_search
    )

    return {
        "code": 200,
        "message": "success",
        "data": {
            "query": request.query,
            "results": results,
            "total": len(results),
            "search_method": "faiss-hnsw" if index_metadata["index_type"] == "HNSW" else "faiss-ivf"
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


@router.post("/config/hnsw")
async def update_hnsw_config(
    M: int = HNSWConfig.M,
    ef_construction: int = HNSWConfig.EF_CONSTRUCTION,
    ef_search: int = HNSWConfig.EF_SEARCH
):
    """更新 HNSW 配置"""
    global faiss_index, index_metadata
    
    # 更新配置
    HNSWConfig.M = M
    HNSWConfig.EF_CONSTRUCTION = ef_construction
    HNSWConfig.EF_SEARCH = ef_search
    
    # 如果索引已存在，更新 efSearch
    if faiss_index is not None and hasattr(faiss_index, 'hnsw'):
        faiss_index.hnsw.efSearch = ef_search
    
    index_metadata["hnsw_config"] = {
        "M": M,
        "ef_construction": ef_construction,
        "ef_search": ef_search
    }
    
    return {
        "code": 200,
        "message": "HNSW 配置已更新",
        "data": index_metadata["hnsw_config"]
    }


@router.delete("/reset")
async def reset_index():
    """重置索引"""
    global faiss_index, index_metadata, doc_id_to_index, index_to_doc_id

    faiss_index = None
    index_metadata = {
        "total_vectors": 0,
        "dimension": settings.FAISS_DIMENSION,
        "index_type": "HNSW",
        "created_at": None,
        "last_updated": None,
        "hnsw_config": {
            "M": HNSWConfig.M,
            "ef_construction": HNSWConfig.EF_CONSTRUCTION,
            "ef_search": HNSWConfig.EF_SEARCH
        }
    }
    doc_id_to_index = {}
    index_to_doc_id = {}

    return {
        "code": 200,
        "message": "索引已重置",
        "data": {"total_vectors": 0}
    }


# ==================== 性能优化建议 ====================
@router.get("/optimization/tips")
async def get_optimization_tips():
    """获取性能优化建议"""
    return {
        "code": 200,
        "data": {
            "hnsw": {
                "description": "HNSW 索引适合实时检索场景",
                "advantages": [
                    "检索速度极快 (微秒级)",
                    "召回率高 (>95%)",
                    "无需训练"
                ],
                "disadvantages": [
                    "内存占用较大",
                    "构建时间较长"
                ],
                "tuning": {
                    "M": "越大图越稠密，检索越准确但内存占用越大 (推荐 16-64)",
                    "ef_construction": "越大构建越慢但索引质量越高 (推荐 100-400)",
                    "ef_search": "越大检索越准确但延迟越高 (推荐 32-128)"
                }
            },
            "ivf_pq": {
                "description": "IVF-PQ 索引适合大数据集",
                "advantages": [
                    "内存占用小",
                    "适合百万级向量"
                ],
                "disadvantages": [
                    "需要训练",
                    "精度略低"
                ],
                "tuning": {
                    "nlist": "聚类数，推荐 √N (N 为向量数)",
                    "nprobe": "搜索聚类数，越大越准确但越慢 (推荐 10-100)"
                }
            }
        }
    }


# ==================== 生命周期管理 ====================
@router.on_event("startup")
async def startup_load_index():
    """启动时自动加载索引 - 修复 OFF-001 问题"""
    success = load_index_from_disk()
    if not success:
        print("FAISS 索引加载失败，将在首次使用时创建")


@router.on_event("shutdown")
async def shutdown_save_index():
    """关闭时自动保存索引 - 修复 OFF-001 问题"""
    save_index_to_disk()
