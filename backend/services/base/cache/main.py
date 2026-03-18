"""Redis缓存服务 - L1/L2缓存策略"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Optional
from datetime import datetime
import json
import hashlib
import logging

router = APIRouter(prefix="/cache", tags=["Cache"])

# Redis客户端
from common.database.redis import redis_client
import redis.asyncio as redis

# 内存L1缓存
L1_CACHE = {}
L1_MAX_SIZE = 100
L1_TTL = 60  # 1分钟

# L2 Redis缓存配置
L2_MAX_SIZE = 1000
L2_TTL = 3600  # 1小时


class CacheRequest(BaseModel):
    key: str
    value: Any
    ttl: int = 3600


class CacheResponse(BaseModel):
    key: str
    value: Any
    cache_type: str


def get_cache_key(key: str) -> str:
    """生成缓存键"""
    return hashlib.md5(key.encode()).hexdigest()


def get_from_l1(key: str) -> Optional[Any]:
    """从L1内存缓存获取"""
    cache_key = get_cache_key(key)
    if cache_key in L1_CACHE:
        item = L1_CACHE[cache_key]
        if (datetime.utcnow() - item["timestamp"]).seconds < L1_TTL:
            return item["value"]
        else:
            del L1_CACHE[cache_key]
    return None


def set_to_l1(key: str, value: Any):
    """设置L1内存缓存"""
    cache_key = get_cache_key(key)
    if len(L1_CACHE) >= L1_MAX_SIZE:
        oldest = min(L1_CACHE.items(), key=lambda x: x[1]["timestamp"])
        del L1_CACHE[oldest[0]]
    
    L1_CACHE[cache_key] = {"value": value, "timestamp": datetime.utcnow()}


async def get_from_l2(key: str) -> Optional[Any]:
    """从L2 Redis缓存获取"""
    cache_key = get_cache_key(key)
    try:
        r = await redis_client.connect()
        value = await r.get(cache_key)
        if value:
            return json.loads(value)
    except Exception as e:
        logging.warning(f"Redis获取失败: {e}")
    return None


async def set_to_l2(key: str, value: Any, ttl: int = L2_TTL):
    """设置L2 Redis缓存"""
    cache_key = get_cache_key(key)
    try:
        r = await redis_client.connect()
        await r.setex(cache_key, ttl, json.dumps(value))
    except Exception as e:
        logging.warning(f"Redis设置失败: {e}")


async def delete_from_l2(key: str):
    """从L2 Redis缓存删除"""
    cache_key = get_cache_key(key)
    try:
        r = await redis_client.connect()
        await r.delete(cache_key)
    except Exception as e:
        logging.warning(f"Redis删除失败: {e}")


@router.post("/set")
async def set_cache(request: CacheRequest):
    """设置缓存 - L1 + L2"""
    key = request.key
    
    # 设置L1缓存
    set_to_l1(key, request.value)
    
    # 设置L2缓存
    await set_to_l2(key, request.value, request.ttl)
    
    return {"code": 200, "message": "已缓存", "data": {"key": request.key, "ttl": request.ttl}}


@router.get("/get/{key}")
async def get_cache(key: str):
    """获取缓存 - L1优先，然后L2"""
    # 先尝试L1
    value = get_from_l1(key)
    if value is not None:
        return {"code": 200, "message": "命中L1缓存", "data": {"key": key, "value": value, "cache_type": "L1"}}
    
    # 再尝试L2
    value = await get_from_l2(key)
    if value is not None:
        # 回填L1
        set_to_l1(key, value)
        return {"code": 200, "message": "命中L2缓存", "data": {"key": key, "value": value, "cache_type": "L2"}}
    
    return {"code": 404, "message": "缓存未命中", "data": {"key": key}}


@router.delete("/{key}")
async def delete_cache(key: str):
    """删除缓存"""
    cache_key = get_cache_key(key)
    
    # 删除L1
    if cache_key in L1_CACHE:
        del L1_CACHE[cache_key]
    
    # 删除L2
    await delete_from_l2(key)
    
    return {"code": 200, "message": "已删除"}


@router.get("/stats")
async def get_cache_stats():
    """获取缓存统计"""
    # 获取Redis信息
    redis_info = {"connected": False}
    try:
        r = await redis_client.connect()
        await r.ping()
        redis_info = {"connected": True}
    except Exception as e:
        redis_info = {"connected": False, "error": str(e)}
    
    return {
        "code": 200,
        "data": {
            "l1_size": len(L1_CACHE),
            "l1_max": L1_MAX_SIZE,
            "l1_ttl": L1_TTL,
            "l2_max": L2_MAX_SIZE,
            "l2_ttl": L2_TTL,
            "redis": redis_info
        }
    }


@router.post("/clear")
async def clear_cache():
    """清空所有缓存"""
    global L1_CACHE
    L1_CACHE = {}
    
    try:
        r = await redis_client.connect()
        await r.flushdb()
    except Exception as e:
        logging.warning(f"Redis清空失败: {e}")
    
    return {"code": 200, "message": "缓存已清空"}
