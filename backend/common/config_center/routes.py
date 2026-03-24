"""配置中心 API 路由 - P3-001

提供配置的 CRUD 操作和变更历史查询。
"""

from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime
import json

from .main import config_center, ConfigValue, DEFAULT_CONFIG

router = APIRouter(prefix="/config", tags=["Config Center"])


# ==================== 请求/响应模型 ====================
class ConfigGetRequest(BaseModel):
    """获取配置请求"""
    key: str = Field(..., description="配置键（点分隔，如 rag.fusion.bm25_weight）")
    include_metadata: bool = Field(False, description="是否包含元数据（版本、更新时间等）")


class ConfigGetResponse(BaseModel):
    """获取配置响应"""
    code: int = 200
    message: str = "success"
    data: Dict[str, Any]


class ConfigSetRequest(BaseModel):
    """设置配置请求"""
    key: str = Field(..., description="配置键")
    value: Any = Field(..., description="配置值")
    updated_by: str = Field("api", description="更新者标识")


class ConfigItem(BaseModel):
    """配置项"""
    key: str
    value: Any
    version: Optional[int] = None
    updated_at: Optional[str] = None
    updated_by: Optional[str] = None


class ConfigListResponse(BaseModel):
    """配置列表响应"""
    code: int = 200
    message: str = "success"
    data: List[ConfigItem]
    total: int


class ConfigHistoryItem(BaseModel):
    """配置历史项"""
    key: str
    old_value: Any
    new_value: Any
    updated_at: str
    updated_by: str


# ==================== API 接口 ====================
@router.get("/", response_model=ConfigGetResponse)
async def get_config_status():
    """获取配置中心状态"""
    return ConfigGetResponse(
        code=200,
        message="success",
        data={
            "status": "initialized" if config_center._initialized else "not_initialized",
            "config_count": len(config_center._config_cache),
            "backend": type(config_center._backend).__name__ if config_center._backend else None,
        }
    )


@router.get("/get", response_model=ConfigGetResponse)
async def get_config_value(
    key: str = Query(..., description="配置键"),
    include_metadata: bool = Query(False, description="是否包含元数据"),
):
    """获取单个配置值"""
    if include_metadata:
        metadata = config_center.get_with_metadata().get(key)
        if metadata:
            return ConfigGetResponse(
                code=200,
                message="success",
                data={
                    "key": key,
                    **metadata,
                }
            )
        else:
            # 返回默认值
            default_value = config_center.get(key)
            return ConfigGetResponse(
                code=200,
                message="success (default value)",
                data={
                    "key": key,
                    "value": default_value,
                    "source": "default",
                }
            )
    else:
        value = config_center.get(key)
        if value is not None:
            return ConfigGetResponse(
                code=200,
                message="success",
                data={
                    "key": key,
                    "value": value,
                }
            )
        else:
            raise HTTPException(status_code=404, detail=f"配置未找到：{key}")


@router.post("/set", response_model=ConfigGetResponse)
async def set_config_value(request: ConfigSetRequest):
    """设置配置值（热更新）"""
    if not config_center._initialized:
        raise HTTPException(status_code=503, detail="配置中心未初始化")
    
    try:
        await config_center.set(
            key=request.key,
            value=request.value,
            updated_by=request.updated_by
        )
        
        return ConfigGetResponse(
            code=200,
            message="配置更新成功",
            data={
                "key": request.key,
                "value": request.value,
                "updated_by": request.updated_by,
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新配置失败：{e}")


@router.get("/list", response_model=ConfigListResponse)
async def list_all_configs(
    prefix: Optional[str] = Query(None, description="配置键前缀过滤"),
    include_metadata: bool = Query(False, description="是否包含元数据"),
):
    """获取所有配置"""
    if include_metadata:
        all_configs = config_center.get_with_metadata()
    else:
        all_configs = config_center.get_all()
    
    # 过滤
    if prefix:
        all_configs = {k: v for k, v in all_configs.items() if k.startswith(prefix)}
    
    # 转换为列表
    items = []
    for key, value_data in all_configs.items():
        if include_metadata and isinstance(value_data, dict):
            items.append(ConfigItem(
                key=key,
                value=value_data.get("value"),
                version=value_data.get("version"),
                updated_at=value_data.get("updated_at"),
                updated_by=value_data.get("updated_by"),
            ))
        else:
            items.append(ConfigItem(key=key, value=value_data))
    
    return ConfigListResponse(
        code=200,
        message="success",
        data=items,
        total=len(items)
    )


@router.get("/defaults", response_model=ConfigGetResponse)
async def get_default_configs():
    """获取默认配置"""
    return ConfigGetResponse(
        code=200,
        message="success",
        data=DEFAULT_CONFIG
    )


@router.post("/refresh", response_model=ConfigGetResponse)
async def refresh_configs():
    """刷新配置（从存储重新加载）"""
    if not config_center._initialized:
        raise HTTPException(status_code=503, detail="配置中心未初始化")
    
    try:
        await config_center.refresh()
        return ConfigGetResponse(
            code=200,
            message="配置刷新成功",
            data={
                "config_count": len(config_center._config_cache),
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"刷新配置失败：{e}")


@router.get("/export", response_model=ConfigGetResponse)
async def export_configs(format: str = Query("json", description="导出格式：json|env")):
    """导出配置"""
    all_configs = config_center.get_all()
    
    if format == "json":
        return ConfigGetResponse(
            code=200,
            message="success",
            data=all_configs
        )
    elif format == "env":
        # 转换为环境变量格式
        env_lines = []
        for key, value in all_configs.items():
            env_key = key.upper().replace(".", "_")
            if isinstance(value, bool):
                env_value = "true" if value else "false"
            elif isinstance(value, (dict, list)):
                env_value = json.dumps(value, ensure_ascii=False)
            else:
                env_value = str(value)
            env_lines.append(f"{env_key}={env_value}")
        
        return ConfigGetResponse(
            code=200,
            message="success",
            data={"env_content": "\n".join(env_lines)}
        )
    else:
        raise HTTPException(status_code=400, detail=f"不支持的导出格式：{format}")


@router.get("/diff", response_model=ConfigGetResponse)
async def diff_with_defaults():
    """比较当前配置与默认配置的差异"""
    current = config_center.get_all()
    defaults = flatten_dict(DEFAULT_CONFIG)
    
    diff = {
        "added": {},      # 当前有但默认没有的
        "removed": {},    # 默认有但当前没有的
        "modified": {},   # 值不同的
    }
    
    # 检查新增和修改
    for key, value in current.items():
        if key not in defaults:
            diff["added"][key] = value
        elif value != defaults[key]:
            diff["modified"][key] = {
                "current": value,
                "default": defaults[key],
            }
    
    # 检查移除
    for key, value in defaults.items():
        if key not in current:
            diff["removed"][key] = value
    
    return ConfigGetResponse(
        code=200,
        message="success",
        data=diff
    )


@router.get("/history/{key}", response_model=List[ConfigHistoryItem])
async def get_config_history(
    key: str,
    limit: int = Query(10, description="返回最近 N 条记录"),
):
    """获取配置变更历史
    
    注意：需要配置变更日志功能支持
    """
    # TODO: 实现配置变更历史记录
    # 目前返回空列表
    return []


@router.post("/validate", response_model=ConfigGetResponse)
async def validate_config(
    key: str = Body(..., description="配置键"),
    value: Any = Body(..., description="配置值"),
):
    """验证配置值是否有效"""
    # TODO: 实现配置验证逻辑
    # 目前只进行基本检查
    
    errors = []
    
    # 检查类型
    if key.endswith("_weight") and isinstance(value, (int, float)):
        if not (0 <= value <= 1):
            errors.append(f"{key} 应该在 0-1 之间")
    
    if key.endswith("_timeout") and isinstance(value, (int, float)):
        if value <= 0:
            errors.append(f"{key} 应该大于 0")
    
    if key.endswith("_size") and isinstance(value, int):
        if value <= 0:
            errors.append(f"{key} 应该大于 0")
    
    return ConfigGetResponse(
        code=200 if not errors else 400,
        message="验证通过" if not errors else "验证失败",
        data={
            "valid": len(errors) == 0,
            "errors": errors,
        }
    )


# ==================== 辅助函数 ====================
def flatten_dict(d: Dict, parent_key: str = '', sep: str = '.') -> Dict:
    """扁平化嵌套字典"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}.{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep).items())
        else:
            items.append((new_key, v))
    return dict(items)
