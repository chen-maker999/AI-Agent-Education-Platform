"""高并发流量管控服务 - 限流与熔断"""

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import time
import asyncio

router = APIRouter(prefix="/flow", tags=["Flow Control"])

# 内存存储的限流数据
rate_limits: Dict[str, dict] = {}
# 熔断器状态
circuit_breakers: Dict[str, dict] = {}


class RateLimitConfig(BaseModel):
    endpoint: str
    max_requests: int = 60  # 每分钟最大请求数
    window_seconds: int = 60
    user_level: bool = True  # 是否按用户限流


class CircuitBreakerConfig(BaseModel):
    service_name: str
    failure_threshold: int = 5  # 失败次数阈值
    timeout_seconds: int = 60  # 熔断超时时间
    half_open_requests: int = 3  # 半开状态允许的请求数


async def check_rate_limit(request: Request, endpoint: str) -> bool:
    """检查请求是否超过限流阈值"""
    client_id = request.client.host if request.client else "unknown"
    key = f"{endpoint}:{client_id}"
    current_time = time.time()
    
    if key not in rate_limits:
        rate_limits[key] = {
            "count": 1,
            "reset_time": current_time + 60
        }
        return True
    
    record = rate_limits[key]
    
    # 检查是否需要重置计数器
    if current_time > record["reset_time"]:
        rate_limits[key] = {
            "count": 1,
            "reset_time": current_time + 60
        }
        return True
    
    # 检查是否超过限流
    if record["count"] >= 60:  # 默认每分钟60次
        return False
    
    record["count"] += 1
    return True


@router.post("/rate-limit")
async def create_rate_limit(config: RateLimitConfig):
    """配置限流规则"""
    key = config.endpoint
    rate_limits[f"config:{key}"] = {
        "endpoint": config.endpoint,
        "max_requests": config.max_requests,
        "window_seconds": config.window_seconds,
        "user_level": config.user_level,
        "created_at": datetime.now().isoformat()
    }
    
    return {"code": 201, "message": "限流规则创建成功", "data": rate_limits[f"config:{key}"]}


@router.get("/rate-limit")
async def list_rate_limits():
    """获取限流规则列表"""
    items = [v for k, v in rate_limits.items() if k.startswith("config:")]
    return {"code": 200, "message": "success", "data": {"items": items, "total": len(items)}}


@router.post("/circuit-breaker")
async def create_circuit_breaker(config: CircuitBreakerConfig):
    """创建熔断器"""
    circuit_breakers[config.service_name] = {
        "service_name": config.service_name,
        "failure_threshold": config.failure_threshold,
        "timeout_seconds": config.timeout_seconds,
        "half_open_requests": config.half_open_requests,
        "state": "closed",  # closed, open, half_open
        "failure_count": 0,
        "last_failure_time": None,
        "created_at": datetime.now().isoformat()
    }
    
    return {"code": 201, "message": "熔断器创建成功", "data": circuit_breakers[config.service_name]}


@router.get("/circuit-breaker/{service_name}")
async def get_circuit_breaker(service_name: str):
    """获取熔断器状态"""
    if service_name not in circuit_breakers:
        raise HTTPException(status_code=404, detail="熔断器不存在")
    
    return {"code": 200, "message": "success", "data": circuit_breakers[service_name]}


@router.post("/circuit-breaker/{service_name}/record-failure")
async def record_failure(service_name: str):
    """记录服务失败"""
    if service_name not in circuit_breakers:
        raise HTTPException(status_code=404, detail="熔断器不存在")
    
    cb = circuit_breakers[service_name]
    cb["failure_count"] += 1
    cb["last_failure_time"] = datetime.now().isoformat()
    
    # 检查是否触发熔断
    if cb["failure_count"] >= cb["failure_threshold"]:
        cb["state"] = "open"
    
    return {"code": 200, "message": "失败记录成功", "data": cb}


@router.post("/circuit-breaker/{service_name}/reset")
async def reset_circuit_breaker(service_name: str):
    """重置熔断器"""
    if service_name not in circuit_breakers:
        raise HTTPException(status_code=404, detail="熔断器不存在")
    
    circuit_breakers[service_name] = {
        **circuit_breakers[service_name],
        "state": "closed",
        "failure_count": 0,
        "last_failure_time": None
    }
    
    return {"code": 200, "message": "熔断器已重置", "data": circuit_breakers[service_name]}


@router.get("/stats")
async def get_flow_stats():
    """获取流量统计"""
    return {
        "code": 200,
        "message": "success",
        "data": {
            "rate_limits": len([k for k in rate_limits.keys() if not k.startswith("config:")]),
            "circuit_breakers": len(circuit_breakers),
            "timestamp": datetime.now().isoformat()
        }
    }


@router.get("/status")
async def get_flow_status():
    """获取流量控制状态"""
    return {
        "code": 200,
        "message": "success",
        "data": {
            "rate_limits_active": len([k for k in rate_limits.keys() if not k.startswith("config:")]),
            "circuit_breakers_active": len(circuit_breakers),
            "timestamp": datetime.now().isoformat()
        }
    }
