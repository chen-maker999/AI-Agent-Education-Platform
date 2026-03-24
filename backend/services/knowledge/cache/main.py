"""缓存服务 (CACHE) - 多级缓存系统：本地 LRU + Redis"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
import hashlib
import json
from functools import lru_cache
import pickle
import numpy as np

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

router = APIRouter(prefix="/cache", tags=["Cache Service"])


# ==================== 配置 ====================
class CacheConfig:
    """缓存配置"""
    # 本地缓存配置
    LRU_MAX_SIZE = 1000  # LRU 最大条目数

    # Redis 缓存配置
    REDIS_HOST = "localhost"
    REDIS_PORT = 6379
    REDIS_DB = 0
    REDIS_PASSWORD = None
    DEFAULT_TTL = 3600  # 默认 1 小时
    KEY_PREFIX = "rag:cache:"
    
    # 查询嵌入缓存配置
    EMBEDDING_CACHE_TTL = 86400  # 嵌入缓存 24 小时
    EMBEDDING_CACHE_KEY_PREFIX = "rag:embedding:"


# ==================== 本地 LRU 缓存 ====================
class LocalLRUCache:
    """本地 LRU 缓存装饰器"""
    
    def __init__(self, max_size: int = CacheConfig.LRU_MAX_SIZE):
        self.max_size = max_size
        self._cache: Dict[str, Any] = {}
        self._access_order: Dict[str, datetime] = {}
        self._stats = {"hits": 0, "misses": 0, "evictions": 0}
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if key in self._cache:
            self._access_order[key] = datetime.utcnow()
            self._stats["hits"] += 1
            return self._cache[key]
        self._stats["misses"] += 1
        return None
    
    def set(self, key: str, value: Any):
        """设置缓存"""
        # 如果缓存已满，删除最久未使用的条目
        if len(self._cache) >= self.max_size and key not in self._cache:
            oldest_key = min(self._access_order.keys(), key=lambda k: self._access_order[k])
            del self._cache[oldest_key]
            del self._access_order[oldest_key]
            self._stats["evictions"] += 1
        
        self._cache[key] = value
        self._access_order[key] = datetime.utcnow()
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        if key in self._cache:
            del self._cache[key]
            del self._access_order[key]
            return True
        return False
    
    def clear(self):
        """清空缓存"""
        self._cache.clear()
        self._access_order.clear()
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        total = self._stats["hits"] + self._stats["misses"]
        return {
            **self._stats,
            "size": len(self._cache),
            "max_size": self.max_size,
            "hit_rate": self._stats["hits"] / max(total, 1)
        }


# 全局本地缓存实例
local_cache = LocalLRUCache()


# ==================== Redis 缓存 ====================
class RedisCache:
    """Redis 缓存封装"""
    
    def __init__(self):
        self._client: Optional[redis.Redis] = None
        self._stats = {"hits": 0, "misses": 0, "errors": 0}
        self._connected = False
    
    def connect(self, host: str = CacheConfig.REDIS_HOST, port: int = CacheConfig.REDIS_PORT, 
                db: int = CacheConfig.REDIS_DB, password: Optional[str] = CacheConfig.REDIS_PASSWORD):
        """连接 Redis"""
        try:
            self._client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=False,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # 测试连接
            self._client.ping()
            self._connected = True
            print(f"[Cache] Redis 连接成功：{host}:{port}")
        except Exception as e:
            print(f"[Cache] Redis 连接失败：{e}")
            self._connected = False
            self._stats["errors"] += 1
    
    def _get_key(self, key: str) -> str:
        """生成带前缀的键"""
        return f"{CacheConfig.KEY_PREFIX}{key}"
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if not self._connected or not self._client:
            return None
        
        try:
            data = self._client.get(self._get_key(key))
            if data:
                self._stats["hits"] += 1
                return pickle.loads(data)
            self._stats["misses"] += 1
            return None
        except Exception as e:
            print(f"[Cache] Redis GET 错误：{e}")
            self._stats["errors"] += 1
            return None
    
    def set(self, key: str, value: Any, ttl: int = CacheConfig.DEFAULT_TTL):
        """设置缓存"""
        if not self._connected or not self._client:
            return False
        
        try:
            data = pickle.dumps(value)
            self._client.setex(self._get_key(key), ttl, data)
            return True
        except Exception as e:
            print(f"[Cache] Redis SET 错误：{e}")
            self._stats["errors"] += 1
            return False
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self._connected or not self._client:
            return False
        
        try:
            self._client.delete(self._get_key(key))
            return True
        except Exception as e:
            print(f"[Cache] Redis DELETE 错误：{e}")
            self._stats["errors"] += 1
            return False
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if not self._connected or not self._client:
            return False
        
        try:
            return self._client.exists(self._get_key(key)) > 0
        except Exception as e:
            print(f"[Cache] Redis EXISTS 错误：{e}")
            self._stats["errors"] += 1
            return False
    
    def clear(self, pattern: str = "*"):
        """清空缓存（支持通配符）"""
        if not self._connected or not self._client:
            return
        
        try:
            keys = self._client.keys(self._get_key(pattern))
            if keys:
                self._client.delete(*keys)
        except Exception as e:
            print(f"[Cache] Redis CLEAR 错误：{e}")
            self._stats["errors"] += 1
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        total = self._stats["hits"] + self._stats["misses"]
        return {
            **self._stats,
            "connected": self._connected,
            "hit_rate": self._stats["hits"] / max(total, 1)
        }
    
    def close(self):
        """关闭连接"""
        if self._client:
            self._client.close()
            self._connected = False


# 全局 Redis 缓存实例
redis_cache = RedisCache()


# ==================== 多级缓存管理器 ====================
class MultiLevelCache:
    """
    多级缓存管理器
    
    层级:
    L1: 本地内存缓存 (LRU) - 最快，容量小
    L2: Redis 缓存 - 较快，容量大，可共享
    """
    
    def __init__(self):
        self.l1_cache = local_cache
        self.l2_cache = redis_cache
        self._stats = {"l1_hits": 0, "l2_hits": 0, "misses": 0}
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存 - 先查 L1，再查 L2"""
        # 1. 查 L1
        value = self.l1_cache.get(key)
        if value is not None:
            self._stats["l1_hits"] += 1
            return value
        
        # 2. 查 L2
        value = self.l2_cache.get(key)
        if value is not None:
            self._stats["l2_hits"] += 1
            # 回写到 L1
            self.l1_cache.set(key, value)
            return value
        
        self._stats["misses"] += 1
        return None
    
    def set(self, key: str, value: Any, ttl: int = CacheConfig.DEFAULT_TTL):
        """设置缓存 - 同时写入 L1 和 L2"""
        # 写入 L1
        self.l1_cache.set(key, value)
        
        # 写入 L2
        self.l2_cache.set(key, value, ttl)
    
    def delete(self, key: str):
        """删除缓存 - 同时删除 L1 和 L2"""
        self.l1_cache.delete(key)
        self.l2_cache.delete(key)
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        total = self._stats["l1_hits"] + self._stats["l2_hits"] + self._stats["misses"]
        return {
            **self._stats,
            "total_requests": total,
            "overall_hit_rate": (self._stats["l1_hits"] + self._stats["l2_hits"]) / max(total, 1),
            "l1_stats": self.l1_cache.get_stats(),
            "l2_stats": self.l2_cache.get_stats()
        }
    
    def clear(self):
        """清空所有缓存"""
        self.l1_cache.clear()
        self.l2_cache.clear()


# 全局多级缓存实例
multi_level_cache = MultiLevelCache()


# ==================== 缓存装饰器 ====================
def cached(ttl: int = CacheConfig.DEFAULT_TTL, use_lru: bool = True):
    """
    缓存装饰器
    
    用法:
        @cached(ttl=3600)
        async def expensive_query(param1, param2):
            ...
    """
    def decorator(func):
        if use_lru:
            # 使用 LRU 缓存
            @lru_cache(maxsize=CacheConfig.LRU_MAX_SIZE)
            def _lru_wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            
            async def wrapper(*args, **kwargs):
                # 生成缓存键
                key_data = f"{func.__name__}:{args}:{kwargs}"
                cache_key = hashlib.md5(key_data.encode()).hexdigest()
                
                # 尝试从多级缓存获取
                cached_value = multi_level_cache.get(cache_key)
                if cached_value is not None:
                    return cached_value
                
                # 执行函数
                result = await func(*args, **kwargs)
                
                # 写入缓存
                multi_level_cache.set(cache_key, result, ttl)
                
                return result
        else:
            async def wrapper(*args, **kwargs):
                # 生成缓存键
                key_data = f"{func.__name__}:{args}:{kwargs}"
                cache_key = hashlib.md5(key_data.encode()).hexdigest()
                
                # 尝试从多级缓存获取
                cached_value = multi_level_cache.get(cache_key)
                if cached_value is not None:
                    return cached_value
                
                # 执行函数
                result = await func(*args, **kwargs)
                
                # 写入缓存
                multi_level_cache.set(cache_key, result, ttl)
                
                return result
        
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    
    return decorator


# ==================== 缓存工具函数 ====================
def compute_embedding_cache_key(text: str) -> str:
    """计算嵌入缓存键"""
    return f"embedding:{hashlib.md5(text.encode()).hexdigest()}"


def compute_search_cache_key(query: str, course_id: Optional[str], top_k: int) -> str:
    """计算搜索缓存键"""
    key_data = f"search:{query}:{course_id}:{top_k}"
    return hashlib.md5(key_data.encode()).hexdigest()


# ==================== API 接口 ====================
class CacheStatsResponse(BaseModel):
    code: int
    data: Dict


@router.get("/stats", response_model=CacheStatsResponse)
async def get_cache_stats():
    """获取缓存统计"""
    return {
        "code": 200,
        "data": multi_level_cache.get_stats()
    }


@router.post("/connect")
async def connect_redis(
    host: str = CacheConfig.REDIS_HOST,
    port: int = CacheConfig.REDIS_PORT,
    db: int = CacheConfig.REDIS_DB,
    password: Optional[str] = CacheConfig.REDIS_PASSWORD
):
    """连接 Redis"""
    redis_cache.connect(host, port, db, password)
    
    if redis_cache._connected:
        return {"code": 200, "message": "Redis 连接成功"}
    else:
        return {"code": 500, "message": "Redis 连接失败，请检查配置"}


@router.delete("/clear")
async def clear_all_cache():
    """清空所有缓存"""
    multi_level_cache.clear()
    return {"code": 200, "message": "缓存已清空"}


@router.delete("/clear/l1")
async def clear_l1_cache():
    """清空 L1 缓存"""
    local_cache.clear()
    return {"code": 200, "message": "L1 缓存已清空"}


@router.delete("/clear/l2")
async def clear_l2_cache():
    """清空 L2 缓存"""
    redis_cache.clear()
    return {"code": 200, "message": "L2 缓存已清空"}


@router.get("/test/{key}")
async def test_cache(key: str):
    """测试缓存"""
    value = multi_level_cache.get(key)
    if value:
        return {"code": 200, "data": {"key": key, "value": value, "cached": True}}
    else:
        return {"code": 200, "data": {"key": key, "cached": False}}


@router.post("/test/{key}")
async def test_cache_set(key: str, value: Dict, ttl: int = 300):
    """测试缓存设置"""
    multi_level_cache.set(key, value, ttl)
    return {"code": 200, "message": "缓存设置成功", "data": {"key": key, "ttl": ttl}}


# ==================== 初始化 ====================
def init_cache():
    """初始化缓存服务"""
    # 自动连接 Redis
    redis_cache.connect()
    print("[Cache] 多级缓存初始化完成")
    print(f"[Cache] - L1 LRU 缓存：最大 {CacheConfig.LRU_MAX_SIZE} 条目")
    print(f"[Cache] - L2 Redis 缓存：{'已连接' if redis_cache._connected else '未连接'}")


# ==================== 查询嵌入缓存 ====================
class EmbeddingCache:
    """
    查询嵌入缓存 - 专门用于缓存查询向量
    
    功能:
    - 缓存查询文本的嵌入向量，避免重复计算
    - 使用 Redis 持久化存储，支持分布式共享
    - 支持批量操作
    
    缓存键格式：rag:embedding:{md5_hash}
    """

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis = redis_client or redis_cache._client
        self._stats = {"hits": 0, "misses": 0, "errors": 0}

    def _compute_key(self, text: str) -> str:
        """计算缓存键"""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        return f"{CacheConfig.EMBEDDING_CACHE_KEY_PREFIX}{text_hash}"

    def get(self, text: str) -> Optional[np.ndarray]:
        """获取缓存的嵌入向量"""
        if not self.redis:
            return None

        try:
            key = self._compute_key(text)
            data = self.redis.get(key)
            if data:
                # 解压缩并恢复向量
                vector = np.frombuffer(pickle.loads(data), dtype=np.float32)
                self._stats["hits"] += 1
                return vector
            self._stats["misses"] += 1
            return None
        except Exception as e:
            print(f"[EmbeddingCache] GET 错误：{e}")
            self._stats["errors"] += 1
            return None

    def set(self, text: str, embedding: np.ndarray, ttl: int = CacheConfig.EMBEDDING_CACHE_TTL) -> bool:
        """设置缓存的嵌入向量"""
        if not self.redis:
            return False

        try:
            key = self._compute_key(text)
            # 序列化向量为字节
            data = pickle.dumps(embedding.tobytes())
            self.redis.setex(key, ttl, data)
            return True
        except Exception as e:
            print(f"[EmbeddingCache] SET 错误：{e}")
            self._stats["errors"] += 1
            return False

    def get_batch(self, texts: List[str]) -> Dict[str, Optional[np.ndarray]]:
        """批量获取嵌入向量"""
        if not self.redis:
            return {text: None for text in texts}

        try:
            pipe = self.redis.pipeline()
            keys = [self._compute_key(text) for text in texts]

            for key in keys:
                pipe.get(key)

            results = pipe.execute()

            output = {}
            for text, data in zip(texts, results):
                if data:
                    vector = np.frombuffer(pickle.loads(data), dtype=np.float32)
                    output[text] = vector
                    self._stats["hits"] += 1
                else:
                    output[text] = None
                    self._stats["misses"] += 1

            return output
        except Exception as e:
            print(f"[EmbeddingCache] BATCH GET 错误：{e}")
            self._stats["errors"] += 1
            return {text: None for text in texts}

    def set_batch(self, text_embedding_pairs: List[tuple], ttl: int = CacheConfig.EMBEDDING_CACHE_TTL) -> int:
        """批量设置嵌入向量"""
        if not self.redis:
            return 0

        try:
            pipe = self.redis.pipeline()
            for text, embedding in text_embedding_pairs:
                key = self._compute_key(text)
                data = pickle.dumps(embedding.tobytes())
                pipe.setex(key, ttl, data)

            pipe.execute()
            return len(text_embedding_pairs)
        except Exception as e:
            print(f"[EmbeddingCache] BATCH SET 错误：{e}")
            self._stats["errors"] += 1
            return 0

    def delete(self, text: str) -> bool:
        """删除缓存"""
        if not self.redis:
            return False

        try:
            key = self._compute_key(text)
            self.redis.delete(key)
            return True
        except Exception as e:
            print(f"[EmbeddingCache] DELETE 错误：{e}")
            self._stats["errors"] += 1
            return False

    def clear(self) -> bool:
        """清空所有嵌入缓存"""
        if not self.redis:
            return False

        try:
            pattern = f"{CacheConfig.EMBEDDING_CACHE_KEY_PREFIX}*"
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)
            return True
        except Exception as e:
            print(f"[EmbeddingCache] CLEAR 错误：{e}")
            self._stats["errors"] += 1
            return False

    def get_stats(self) -> Dict:
        """获取统计信息"""
        total = self._stats["hits"] + self._stats["misses"]
        return {
            **self._stats,
            "hit_rate": self._stats["hits"] / max(total, 1) if total > 0 else 0
        }


# 全局嵌入缓存实例
embedding_cache = EmbeddingCache()


# ==================== 嵌入缓存 API ====================
class EmbeddingCacheRequest(BaseModel):
    """嵌入缓存请求"""
    text: str
    embedding: Optional[List[float]] = None


class EmbeddingCacheBatchRequest(BaseModel):
    """批量嵌入缓存请求"""
    texts: List[str]
    embeddings: Optional[List[List[float]]] = None


@router.get("/embedding/stats")
async def get_embedding_cache_stats():
    """获取嵌入缓存统计"""
    return {
        "code": 200,
        "data": embedding_cache.get_stats()
    }


@router.post("/embedding/get")
async def get_embedding(request: EmbeddingCacheRequest):
    """获取缓存的嵌入向量"""
    embedding = embedding_cache.get(request.text)
    if embedding is not None:
        return {
            "code": 200,
            "data": {
                "text": request.text,
                "embedding": embedding.tolist(),
                "cached": True
            }
        }
    return {
        "code": 200,
        "data": {
            "text": request.text,
            "cached": False
        }
    }


@router.post("/embedding/set")
async def set_embedding(request: EmbeddingCacheRequest):
    """设置缓存的嵌入向量"""
    if not request.embedding:
        return {"code": 400, "message": "embedding 不能为空"}

    import numpy as np
    embedding = np.array(request.embedding, dtype=np.float32)
    success = embedding_cache.set(request.text, embedding)
    return {
        "code": 200 if success else 500,
        "message": "嵌入缓存设置成功" if success else "设置失败"
    }


@router.post("/embedding/get/batch")
async def get_embedding_batch(request: EmbeddingCacheBatchRequest):
    """批量获取嵌入向量"""
    results = embedding_cache.get_batch(request.texts)
    output = []
    for text, embedding in results.items():
        output.append({
            "text": text,
            "embedding": embedding.tolist() if embedding is not None else None,
            "cached": embedding is not None
        })
    return {
        "code": 200,
        "data": {
            "results": output,
            "stats": embedding_cache.get_stats()
        }
    }


@router.post("/embedding/set/batch")
async def set_embedding_batch(request: EmbeddingCacheBatchRequest):
    """批量设置嵌入向量"""
    if not request.embeddings or len(request.embeddings) != len(request.texts):
        return {"code": 400, "message": "embeddings 数量必须与 texts 一致"}

    import numpy as np
    pairs = [
        (text, np.array(emb, dtype=np.float32))
        for text, emb in zip(request.texts, request.embeddings)
    ]
    count = embedding_cache.set_batch(pairs)
    return {
        "code": 200,
        "message": f"成功缓存 {count} 个嵌入向量"
    }


@router.delete("/embedding/clear")
async def clear_embedding_cache():
    """清空嵌入缓存"""
    success = embedding_cache.clear()
    return {
        "code": 200 if success else 500,
        "message": "嵌入缓存已清空" if success else "清空失败"
    }
