"""统一配置中心服务"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

router = APIRouter(prefix="/config", tags=["Configuration Center"])

# 内存存储的配置
configs_db: Dict[str, dict] = {}


class ConfigItem(BaseModel):
    key: str
    value: Any
    env: str = "development"  # development, test, production
    group: Optional[str] = None  # 课程/平台分组
    description: Optional[str] = None
    metadata: Optional[Dict] = {}


class ConfigUpdate(BaseModel):
    value: Any
    description: Optional[str] = None


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_config(config: ConfigItem):
    """创建配置项"""
    config_key = f"{config.env}:{config.group or 'default'}:{config.key}"
    
    configs_db[config_key] = {
        "id": str(uuid.uuid4()),
        "key": config.key,
        "value": config.value,
        "env": config.env,
        "group": config.group,
        "description": config.description or "",
        "metadata": config.metadata or {},
        "version": 1,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    return {"code": 201, "message": "配置创建成功", "data": configs_db[config_key]}


@router.get("/{env}/{key}")
async def get_config(env: str, key: str, group: Optional[str] = None):
    """获取配置项"""
    config_key = f"{env}:{group or 'default'}:{key}"
    
    if config_key not in configs_db:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    return {"code": 200, "message": "success", "data": configs_db[config_key]}


@router.put("/{env}/{key}")
async def update_config(env: str, key: str, update: ConfigUpdate, group: Optional[str] = None):
    """更新配置项（支持热更新）"""
    config_key = f"{env}:{group or 'default'}:{key}"
    
    if config_key not in configs_db:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    configs_db[config_key]["value"] = update.value
    configs_db[config_key]["version"] += 1
    configs_db[config_key]["updated_at"] = datetime.now().isoformat()
    if update.description:
        configs_db[config_key]["description"] = update.description
    
    return {"code": 200, "message": "配置更新成功", "data": configs_db[config_key]}


@router.delete("/{env}/{key}")
async def delete_config(env: str, key: str, group: Optional[str] = None):
    """删除配置项"""
    config_key = f"{env}:{group or 'default'}:{key}"
    
    if config_key in configs_db:
        del configs_db[config_key]
        return {"code": 200, "message": "配置删除成功"}
    
    raise HTTPException(status_code=404, detail="配置不存在")


@router.get("/")
async def list_configs(env: Optional[str] = None, group: Optional[str] = None):
    """获取配置列表"""
    items = []
    for config in configs_db.values():
        if (env is None or config["env"] == env) and (group is None or config["group"] == group):
            items.append(config)
    
    return {"code": 200, "message": "success", "data": {"items": items, "total": len(items)}}


@router.get("/groups")
async def list_groups():
    """获取配置分组列表"""
    groups = set()
    for config in configs_db.values():
        if config["group"]:
            groups.add(config["group"])
    
    return {"code": 200, "message": "success", "data": {"items": list(groups), "total": len(groups)}}


@router.get("/{env}/{key}/history")
async def config_history(env: str, key: str, group: Optional[str] = None):
    """获取配置变更历史"""
    # 简化的版本历史（实际应该存储在数据库中）
    config_key = f"{env}:{group or 'default'}:{key}"
    
    if config_key not in configs_db:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    config = configs_db[config_key]
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "items": [
                {
                    "version": config["version"],
                    "value": config["value"],
                    "updated_at": config["updated_at"]
                }
            ]
        }
    }
