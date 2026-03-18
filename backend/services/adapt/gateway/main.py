"""ADAPT - Third-party platform gateway service."""

from uuid import uuid4
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel
from common.models.response import ResponseModel

router = APIRouter(prefix="/adapt/gateway", tags=["Platform Adapt"])

# Platform adapters storage
platform_configs = {}


class PlatformConfig(BaseModel):
    platform: str
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    webhook_url: Optional[str] = None
    enabled: bool = True


@router.get("/platforms", response_model=ResponseModel)
async def list_platforms():
    """List supported platforms."""
    return ResponseModel(
        code=200,
        message="success",
        data={
            "platforms": [
                {"id": "chaoxing", "name": "超星学习通", "status": "supported"},
                {"id": "dingtalk", "name": "钉钉", "status": "supported"},
                {"id": "mooc", "name": "中国大学MOOC", "status": "supported"},
                {"id": "other", "name": "其他平台", "status": "beta"}
            ]
        }
    )


@router.post("/config/{platform}", response_model=ResponseModel)
async def configure_platform(platform: str, config: PlatformConfig):
    """Configure platform adapter."""
    platform_configs[platform] = config.model_dump()
    return ResponseModel(code=200, message="配置保存成功", data=config)


@router.get("/config/{platform}", response_model=ResponseModel)
async def get_platform_config(platform: str):
    """Get platform configuration."""
    if platform not in platform_configs:
        raise HTTPException(status_code=404, detail="Platform not configured")
    return ResponseModel(code=200, message="success", data=platform_configs[platform])


@router.post("/sync/{platform}", response_model=ResponseModel)
async def sync_platform_data(platform: str):
    """Trigger data synchronization with platform."""
    return ResponseModel(
        code=200,
        message="同步任务已启动",
        data={
            "task_id": str(uuid4()),
            "platform": platform,
            "status": "pending"
        }
    )


@router.get("/status/{platform}", response_model=ResponseModel)
async def get_platform_status(platform: str):
    """Get platform connection status."""
    return ResponseModel(
        code=200,
        message="success",
        data={
            "platform": platform,
            "connected": platform in platform_configs,
            "last_sync": datetime.utcnow().isoformat()
        }
    )
