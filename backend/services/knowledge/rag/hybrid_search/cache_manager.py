"""
查询缓存管理器 - LRU 缓存 + TTL 过期

策略:
- LRU 缓存 (最近使用的查询)
- TTL 过期 (2 小时，P11 优化：从 3600 提升至 7200)
- 按 course_id 分组缓存
- 内存限制 (最多 10000 个查询)
"""

import asyncio
import logging
import hashlib
import numpy as np
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
from collections import OrderedDict

logger = logging.getLogger("query_cache")


class CacheEntry:
    """缓存条目"""

    def __init__(self, query: str, embedding: np.ndarray, course_id: Optional[str] = None):
        self.query = query
        self.embedding = embedding
        self.course_id = course_id
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()
        self.access_count = 0

    def is_expired(self, ttl: int) -> bool:
        """检查是否过期"""
        age = (datetime.now() - self.created_at).total_seconds()
        return age > ttl

    def touch(self):
        """更新访问时间"""
        self.last_accessed = datetime.now()
        self.access_count += 1


class QueryCacheManager:
    """
    查询向量缓存管理器

    使用 LRU 算法管理缓存，支持 TTL 过期
    """

    def __init__(self,
                 max_size: int = 10000,
                 ttl: int = 7200,  # P11 优化：从 3600 提升至 7200 (2 小时)
                 cleanup_interval: int = 300):
        """
        Args:
            max_size: 最大缓存条目数
            ttl: 过期时间 (秒)
            cleanup_interval: 清理间隔 (秒)
        """
        self.max_size = max_size
        self.ttl = ttl
        self.cleanup_interval = cleanup_interval
        
        # 缓存存储：query_hash -> CacheEntry
        self.cache: Dict[str, CacheEntry] = OrderedDict()
        
        # 按课程 ID 分组索引
        self.course_index: Dict[str, List[str]] = {}  # course_id -> [query_hashes]
        
        # 统计信息
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        
        # 锁
        self._lock = asyncio.Lock()
        
        # 清理任务
        self._cleanup_task: Optional[asyncio.Task] = None
    
    def _compute_hash(self, query: str, course_id: Optional[str] = None) -> str:
        """计算查询哈希"""
        key = f"{query}:{course_id or 'default'}"
        return hashlib.md5(key.encode()).hexdigest()
    
    async def get(self, 
                  query: str, 
                  course_id: Optional[str] = None) -> Optional[np.ndarray]:
        """
        获取缓存的查询向量
        
        Args:
            query: 查询文本
            course_id: 课程 ID
        
        Returns:
            缓存的向量，如果不存在或已过期则返回 None
        """
        async with self._lock:
            query_hash = self._compute_hash(query, course_id)
            
            if query_hash not in self.cache:
                self.misses += 1
                return None
            
            entry = self.cache[query_hash]
            
            # 检查过期
            if entry.is_expired(self.ttl):
                await self._remove_entry(query_hash)
                self.misses += 1
                return None
            
            # 更新 LRU
            self.cache.move_to_end(query_hash)
            entry.touch()
            self.hits += 1
            
            return entry.embedding.copy()
    
    async def set(self, 
                  query: str, 
                  embedding: np.ndarray,
                  course_id: Optional[str] = None):
        """
        缓存查询向量
        
        Args:
            query: 查询文本
            embedding: 查询向量
            course_id: 课程 ID
        """
        async with self._lock:
            query_hash = self._compute_hash(query, course_id)
            
            # 如果已存在，先移除
            if query_hash in self.cache:
                await self._remove_entry(query_hash)
            
            # 如果超出大小限制，移除最旧的
            while len(self.cache) >= self.max_size:
                oldest_hash = next(iter(self.cache))
                await self._remove_entry(oldest_hash)
            
            # 添加新条目
            entry = CacheEntry(query, embedding, course_id)
            self.cache[query_hash] = entry
            self.cache.move_to_end(query_hash)
            
            # 更新课程索引
            cid = course_id or "default"
            if cid not in self.course_index:
                self.course_index[cid] = []
            if query_hash not in self.course_index[cid]:
                self.course_index[cid].append(query_hash)
    
    async def _remove_entry(self, query_hash: str):
        """移除缓存条目"""
        if query_hash in self.cache:
            entry = self.cache[query_hash]
            course_id = entry.course_id or "default"
            
            # 从课程索引移除
            if course_id in self.course_index:
                if query_hash in self.course_index[course_id]:
                    self.course_index[course_id].remove(query_hash)
            
            # 删除条目
            del self.cache[query_hash]
            self.evictions += 1
    
    async def remove(self, query: str, course_id: Optional[str] = None):
        """移除特定查询的缓存"""
        async with self._lock:
            query_hash = self._compute_hash(query, course_id)
            await self._remove_entry(query_hash)
    
    async def clear(self, course_id: Optional[str] = None):
        """
        清空缓存
        
        Args:
            course_id: 如果指定，只清空该课程的缓存
        """
        async with self._lock:
            if course_id is None:
                # 清空所有
                self.cache.clear()
                self.course_index.clear()
            else:
                # 清空指定课程
                if course_id in self.course_index:
                    for query_hash in self.course_index[course_id]:
                        if query_hash in self.cache:
                            del self.cache[query_hash]
                    del self.course_index[course_id]
    
    async def cleanup(self) -> int:
        """
        清理过期缓存
        
        Returns:
            清理的条目数
        """
        async with self._lock:
            expired_hashes = []
            
            for query_hash, entry in self.cache.items():
                if entry.is_expired(self.ttl):
                    expired_hashes.append(query_hash)
            
            for query_hash in expired_hashes:
                await self._remove_entry(query_hash)
            
            if expired_hashes:
                logger.debug(f"清理过期缓存：{len(expired_hashes)} 条")
            
            return len(expired_hashes)
    
    async def start_cleanup_task(self):
        """启动后台清理任务"""
        async def cleanup_loop():
            while True:
                await asyncio.sleep(self.cleanup_interval)
                try:
                    await self.cleanup()
                except Exception as e:
                    logger.error(f"缓存清理失败：{e}")
        
        self._cleanup_task = asyncio.create_task(cleanup_loop())
        logger.info(f"缓存清理任务已启动 (间隔：{self.cleanup_interval}s)")
    
    async def stop_cleanup_task(self):
        """停止后台清理任务"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            logger.info("缓存清理任务已停止")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0
        
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "hit_rate": round(hit_rate, 3),
            "ttl": self.ttl,
            "course_count": len(self.course_index)
        }
