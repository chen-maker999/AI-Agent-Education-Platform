"""
语义缓存服务 (SEMANTIC CACHE)

P11 优化:
1. 基于向量相似度的缓存复用
2. 支持近似查询匹配
3. 智能缓存过期策略
4. 缓存预热支持
"""

import logging
import hashlib
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from pydantic import BaseModel
from fastapi import APIRouter
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cache", tags=["Semantic Cache"])


# ==================== 数据模型 ====================

class CacheEntry(BaseModel):
    """缓存条目"""
    key: str
    query: str
    query_embedding: Optional[List[float]] = None
    results: List[Dict[str, Any]]
    created_at: datetime
    last_accessed: datetime
    ttl: int  # 秒
    hit_count: int = 0
    similarity_threshold: float = 0.85


class SemanticCacheConfig(BaseModel):
    """语义缓存配置"""
    max_size: int = 1000
    default_ttl: int = 7200  # 2 小时 (P11 优化：从 3600 提升至 7200)
    similarity_threshold: float = 0.8  # P11 优化：从 0.85 降至 0.8，提高缓存命中率
    cleanup_interval: int = 300  # 5 分钟


# ==================== 语义缓存核心类 ====================

class SemanticCache:
    """
    语义缓存
    
    特性:
    1. 基于向量相似度的近似匹配
    2. LRU 淘汰策略
    3. 自动过期清理
    4. 缓存命中率统计
    """
    
    def __init__(self, config: SemanticCacheConfig = None):
        self.config = config or SemanticCacheConfig()
        
        # 缓存存储：key → CacheEntry
        self._cache: Dict[str, CacheEntry] = {}
        
        # 向量索引 (用于相似度搜索)
        self._embedding_index: Dict[str, np.ndarray] = {}
        
        # 统计信息
        self._hits = 0
        self._misses = 0
        self._total_queries = 0
        
        # 清理任务
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self):
        """启动缓存服务"""
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info(f"语义缓存已启动，最大容量：{self.config.max_size}")
    
    async def stop(self):
        """停止缓存服务"""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        logger.info("语义缓存已停止")
    
    async def get(
        self, 
        query: str, 
        query_embedding: Optional[np.ndarray] = None,
        use_semantic: bool = True
    ) -> Optional[List[Dict[str, Any]]]:
        """
        从缓存获取结果
        
        Args:
            query: 查询文本
            query_embedding: 查询向量 (用于语义匹配)
            use_semantic: 是否使用语义匹配
        
        Returns:
            缓存的结果，如果未命中则返回 None
        """
        self._total_queries += 1
        
        # 1. 精确匹配 (MD5)
        exact_key = hashlib.md5(query.encode()).hexdigest()
        
        if exact_key in self._cache:
            entry = self._cache[exact_key]
            
            # 检查是否过期
            if self._is_expired(entry):
                await self._remove(exact_key)
                self._misses += 1
                return None
            
            # 更新访问时间和命中计数
            entry.last_accessed = datetime.utcnow()
            entry.hit_count += 1
            self._hits += 1
            
            logger.debug(f"缓存精确命中：{query[:20]}...")
            return entry.results
        
        # 2. 语义匹配 (向量相似度)
        if use_semantic and query_embedding is not None:
            similar_key = await self._find_similar(query_embedding)
            
            if similar_key:
                entry = self._cache[similar_key]
                
                # 检查是否过期
                if self._is_expired(entry):
                    await self._remove(similar_key)
                    self._misses += 1
                    return None
                
                # 更新访问信息
                entry.last_accessed = datetime.utcnow()
                entry.hit_count += 1
                self._hits += 1
                
                logger.debug(f"缓存语义命中：{query[:20]}... (相似度>{self.config.similarity_threshold})")
                return entry.results
        
        self._misses += 1
        return None
    
    async def set(
        self,
        query: str,
        results: List[Dict[str, Any]],
        query_embedding: Optional[np.ndarray] = None,
        ttl: Optional[int] = None
    ):
        """
        设置缓存
        
        Args:
            query: 查询文本
            results: 缓存的结果
            query_embedding: 查询向量
            ttl: 过期时间 (秒)
        """
        key = hashlib.md5(query.encode()).hexdigest()
        
        # 如果缓存已满，淘汰最少使用的条目
        if len(self._cache) >= self.config.max_size:
            await self._evict_lru()
        
        # 创建缓存条目
        entry = CacheEntry(
            key=key,
            query=query,
            query_embedding=query_embedding.tolist() if query_embedding is not None else None,
            results=results,
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
            ttl=ttl or self.config.default_ttl,
            hit_count=0,
            similarity_threshold=self.config.similarity_threshold
        )
        
        self._cache[key] = entry
        
        # 添加到向量索引
        if query_embedding is not None:
            self._embedding_index[key] = query_embedding
        
        logger.debug(f"缓存已设置：{query[:20]}...")
    
    async def _find_similar(self, query_embedding: np.ndarray) -> Optional[str]:
        """
        查找最相似的缓存条目
        
        使用余弦相似度
        """
        if not self._embedding_index:
            return None
        
        best_key = None
        best_similarity = self.config.similarity_threshold
        
        for key, stored_embedding in self._embedding_index.items():
            # 计算余弦相似度
            similarity = self._cosine_similarity(query_embedding, stored_embedding)
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_key = key
        
        if best_key and best_key in self._cache:
            logger.debug(f"找到相似缓存，相似度：{best_similarity:.3f}")
            return best_key
        
        return None
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """计算余弦相似度"""
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot_product / (norm_a * norm_b)
    
    def _is_expired(self, entry: CacheEntry) -> bool:
        """检查缓存条目是否过期"""
        age = (datetime.utcnow() - entry.created_at).total_seconds()
        return age > entry.ttl
    
    async def _remove(self, key: str):
        """删除缓存条目"""
        if key in self._cache:
            del self._cache[key]
        
        if key in self._embedding_index:
            del self._embedding_index[key]
    
    async def _evict_lru(self):
        """淘汰最少使用的条目"""
        if not self._cache:
            return
        
        # 找到最少使用的条目
        lru_key = min(
            self._cache.keys(),
            key=lambda k: (
                self._cache[k].hit_count,
                self._cache[k].last_accessed
            )
        )
        
        await self._remove(lru_key)
        logger.debug(f"淘汰 LRU 缓存：{lru_key[:10]}...")
    
    async def _cleanup_loop(self):
        """定期清理过期缓存"""
        while self._running:
            try:
                await asyncio.sleep(self.config.cleanup_interval)
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"缓存清理失败：{e}")
    
    async def _cleanup_expired(self):
        """清理所有过期缓存"""
        expired_keys = [
            key for key, entry in self._cache.items()
            if self._is_expired(entry)
        ]
        
        for key in expired_keys:
            await self._remove(key)
        
        if expired_keys:
            logger.info(f"清理 {len(expired_keys)} 个过期缓存条目")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        hit_rate = self._hits / self._total_queries if self._total_queries > 0 else 0.0
        
        return {
            "size": len(self._cache),
            "max_size": self.config.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "total_queries": self._total_queries,
            "hit_rate": hit_rate,
            "embedding_index_size": len(self._embedding_index)
        }
    
    async def clear(self):
        """清空所有缓存"""
        self._cache.clear()
        self._embedding_index.clear()
        self._hits = 0
        self._misses = 0
        self._total_queries = 0
        logger.info("缓存已清空")
    
    async def warmup(self, queries: List[Dict[str, Any]]):
        """
        缓存预热
        
        Args:
            queries: 预热的查询列表，每个包含 query 和 results
        """
        logger.info(f"开始缓存预热，共 {len(queries)} 个查询")
        
        for item in queries:
            query = item.get("query")
            results = item.get("results", [])
            
            if query:
                # 计算查询向量
                try:
                    from services.knowledge.embedding.main import generate_embeddings
                    embeddings = await generate_embeddings([query])
                    embedding = np.array(embeddings[0]).astype('float32')
                except Exception as e:
                    logger.error(f"预热时计算嵌入失败：{e}")
                    embedding = None
                
                await self.set(query, results, embedding)
        
        logger.info("缓存预热完成")


# ==================== 全局缓存实例 ====================

_semantic_cache: Optional[SemanticCache] = None


def get_cache() -> SemanticCache:
    """获取或创建全局缓存实例"""
    global _semantic_cache
    
    if _semantic_cache is None:
        _semantic_cache = SemanticCache()
    
    return _semantic_cache


async def initialize_cache(config: SemanticCacheConfig = None):
    """初始化全局缓存"""
    cache = get_cache()
    cache.config = config or SemanticCacheConfig()
    await cache.start()
    logger.info("全局语义缓存初始化完成")


async def shutdown_cache():
    """关闭全局缓存"""
    cache = get_cache()
    await cache.stop()


# ==================== API 端点 ====================

@router.get("/stats")
async def get_cache_stats():
    """获取缓存统计"""
    cache = get_cache()
    stats = cache.get_stats()
    
    return {
        "code": 200,
        "data": stats
    }


@router.post("/clear")
async def clear_cache():
    """清空缓存"""
    cache = get_cache()
    await cache.clear()
    
    return {
        "code": 200,
        "message": "缓存已清空"
    }


@router.post("/warmup")
async def warmup_cache(queries: List[Dict[str, Any]]):
    """缓存预热"""
    cache = get_cache()
    await cache.warmup(queries)
    
    return {
        "code": 200,
        "message": f"缓存预热完成，加载 {len(queries)} 个查询"
    }


@router.get("/config")
async def get_cache_config():
    """获取缓存配置"""
    cache = get_cache()
    
    return {
        "code": 200,
        "data": {
            "max_size": cache.config.max_size,
            "default_ttl": cache.config.default_ttl,
            "similarity_threshold": cache.config.similarity_threshold,
            "cleanup_interval": cache.config.cleanup_interval
        }
    }


# ==================== 便捷函数 ====================

async def get_cached_results(
    query: str,
    query_embedding: Optional[np.ndarray] = None,
    use_semantic: bool = True
) -> Optional[List[Dict[str, Any]]]:
    """
    便捷函数：从缓存获取结果
    
    用于在其他服务中直接调用
    """
    cache = get_cache()
    return await cache.get(query, query_embedding, use_semantic)


async def set_cache_results(
    query: str,
    results: List[Dict[str, Any]],
    query_embedding: Optional[np.ndarray] = None,
    ttl: Optional[int] = None
):
    """
    便捷函数：设置缓存结果
    
    用于在其他服务中直接调用
    """
    cache = get_cache()
    await cache.set(query, results, query_embedding, ttl)
