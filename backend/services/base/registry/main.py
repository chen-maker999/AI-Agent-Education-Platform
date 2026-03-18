"""服务注册与发现服务 - Consul集成"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List, Dict
import random
import time
from datetime import datetime

router = APIRouter(prefix="/registry", tags=["Service Registry"])

# 内存存储的服务注册表
services_db: Dict[str, dict] = {}


class ServiceRegister(BaseModel):
    service_id: str
    service_name: str
    host: str
    port: int
    metadata: Optional[Dict] = {}
    health_check_url: Optional[str] = None


class ServiceInstance(BaseModel):
    service_id: str
    service_name: str
    host: str
    port: int
    metadata: Dict = {}
    status: str = "healthy"
    weight: int = 100
    last_heartbeat: str = ""


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_service(service: ServiceRegister):
    """注册服务"""
    service_id = f"{service.service_name}-{service.host}-{service.port}"
    services_db[service_id] = {
        "service_id": service_id,
        "service_name": service.service_name,
        "host": service.host,
        "port": service.port,
        "metadata": service.metadata,
        "health_check_url": service.health_check_url,
        "status": "healthy",
        "weight": 100,
        "registered_at": datetime.now().isoformat(),
        "last_heartbeat": datetime.now().isoformat()
    }
    return {"code": 201, "message": "服务注册成功", "data": {"service_id": service_id}}


@router.delete("/register/{service_id}")
async def deregister_service(service_id: str):
    """注销服务"""
    if service_id in services_db:
        del services_db[service_id]
        return {"code": 200, "message": "服务注销成功"}
    raise HTTPException(status_code=404, detail="服务不存在")


@router.get("/services")
async def list_services():
    """获取所有服务列表"""
    services = []
    for svc in services_db.values():
        services.append({
            "service_id": svc["service_id"],
            "service_name": svc["service_name"],
            "host": svc["host"],
            "port": svc["port"],
            "status": svc["status"],
            "registered_at": svc["registered_at"]
        })
    return {"code": 200, "message": "success", "data": {"items": services, "total": len(services)}}


@router.get("/services/{service_name}")
async def discover_service(service_name: str):
    """服务发现 - 获取健康的服务实例"""
    instances = [s for s in services_db.values() 
                if s["service_name"] == service_name and s["status"] == "healthy"]
    
    if not instances:
        raise HTTPException(status_code=404, detail="无可用的服务实例")
    
    # 简单的加权随机负载均衡
    total_weight = sum(i["weight"] for i in instances)
    r = random.randint(0, total_weight)
    cumsum = 0
    selected = instances[0]
    for inst in instances:
        cumsum += inst["weight"]
        if r <= cumsum:
            selected = inst
            break
    
    return {
        "code": 200, 
        "message": "success", 
        "data": {
            "host": selected["host"],
            "port": selected["port"],
            "metadata": selected["metadata"]
        }
    }


@router.post("/heartbeat/{service_id}")
async def heartbeat(service_id: str):
    """服务心跳"""
    if service_id in services_db:
        services_db[service_id]["last_heartbeat"] = datetime.now().isoformat()
        services_db[service_id]["status"] = "healthy"
        return {"code": 200, "message": "心跳更新成功"}
    raise HTTPException(status_code=404, detail="服务不存在")


@router.get("/health/{service_id}")
async def service_health(service_id: str):
    """获取服务健康状态"""
    if service_id not in services_db:
        raise HTTPException(status_code=404, detail="服务不存在")
    
    svc = services_db[service_id]
    last_heartbeat = datetime.fromisoformat(svc["last_heartbeat"])
    seconds_since_heartbeat = (datetime.now() - last_heartbeat).seconds
    
    # 超过30秒没有心跳认为不健康
    if seconds_since_heartbeat > 30:
        svc["status"] = "unhealthy"
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "service_id": service_id,
            "status": svc["status"],
            "last_heartbeat": svc["last_heartbeat"],
            "seconds_since_heartbeat": seconds_since_heartbeat
        }
    }
