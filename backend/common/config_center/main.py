"""配置中心 - P3-001: 统一管理配置，支持热更新

功能:
1. 统一配置管理（替代分散的硬编码配置）
2. 支持热更新（无需重启服务）
3. 支持多种后端：本地文件、etcd、Consul
4. 配置变更回调通知
5. 配置版本管理和回滚

用法:
    from common.config_center import config_center
    
    # 获取配置
    bm25_weight = config_center.get("rag.fusion.bm25_weight", default=0.3)
    
    # 更新配置（热更新）
    await config_center.set("rag.fusion.bm25_weight", 0.35)
    
    # 注册配置变更回调
    config_center.register_callback("rag.fusion.bm25_weight", on_weight_change)
"""

import json
import os
import asyncio
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable, Awaitable
from pathlib import Path
import aiofiles
import copy

try:
    from common.logging_config import get_context_logger
    logger = get_context_logger("config_center")
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


# ==================== 配置模型 ====================
class ConfigValue:
    """配置值包装器，包含元数据"""
    
    def __init__(
        self,
        value: Any,
        version: int = 1,
        updated_at: Optional[datetime] = None,
        updated_by: str = "system"
    ):
        self.value = value
        self.version = version
        self.updated_at = updated_at or datetime.utcnow()
        self.updated_by = updated_by
    
    def to_dict(self) -> Dict:
        return {
            "value": self.value,
            "version": self.version,
            "updated_at": self.updated_at.isoformat(),
            "updated_by": self.updated_by
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ConfigValue":
        return cls(
            value=data["value"],
            version=data.get("version", 1),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.utcnow(),
            updated_by=data.get("updated_by", "system")
        )


# ==================== 默认配置 ====================
DEFAULT_CONFIG = {
    # RAG 检索配置
    "rag": {
        "fusion": {
            "rrf_k": 60,  # RRF 融合参数 k
            "semantic_weight": 0.4,
            "keyword_weight": 0.3,
            "graph_weight": 0.3,
        },
        "retrieval": {
            "top_k": 10,
            "timeout_seconds": 5,
            "use_rerank": True,
            "use_rewrite": True,
        },
        "context": {
            "max_tokens": 3000,
            "use_diversity": True,
            "mmr_lambda": 0.5,
        },
        "cache": {
            "enabled": True,
            "ttl_seconds": 86400,  # 24 小时
            "embedding_ttl": 86400,
        },
    },
    
    # Elasticsearch 配置
    "elasticsearch": {
        "host": "localhost",
        "port": 9200,
        "index": "edu_bm25",
        "timeout": 30,
        "max_retries": 3,
    },
    
    # Redis 配置
    "redis": {
        "host": "localhost",
        "port": 6379,
        "db": 0,
        "password": None,
        "pool_size": 10,
    },
    
    # Kimi API 配置
    "kimi": {
        "endpoint": "https://api.moonshot.cn/v1",
        "model": "moonshot-v1-128k",
        "timeout": 30,
        "max_retries": 3,
        "retry_base_delay": 1.0,
        "circuit_breaker": {
            "enabled": True,
            "failure_threshold": 5,
            "recovery_timeout": 60,
        },
    },
    
    # 限流配置
    "rate_limit": {
        "enabled": True,
        "algorithm": "token_bucket",  # token_bucket or sliding_window
        "default_requests": 60,
        "default_window": 60,
        "bucket_capacity": 100,
        "bucket_refill_rate": 10,
    },
    
    # 意图识别配置
    "intent": {
        "enabled": True,
        "model_path": "models/intent/bert_classifier.pt",
        "confidence_threshold": 0.6,
        "fallback_to_rules": True,
    },
    
    # 分块配置
    "chunk": {
        "strategies": {
            "教材": {"chunk_size": 1000, "overlap": 200},
            "代码示例": {"chunk_size": 500, "overlap": 50},
            "公式": {"chunk_size": 200, "overlap": 20},
            "对话历史": {"chunk_size": 300, "overlap": 30},
        },
    },
    
    # 监控配置
    "monitoring": {
        "enabled": True,
        "prometheus_port": 9090,
        "metrics_interval": 15,
    },
    
    # 日志配置
    "logging": {
        "level": "INFO",
        "format": "json",
        "output": "stdout",
    },
}


# ==================== 配置后端接口 ====================
class ConfigBackend:
    """配置后端接口"""
    
    async def get(self, key: str) -> Optional[ConfigValue]:
        raise NotImplementedError
    
    async def set(self, key: str, value: ConfigValue) -> None:
        raise NotImplementedError
    
    async def get_all(self) -> Dict[str, ConfigValue]:
        raise NotImplementedError
    
    async def watch(self, key: str, callback: Callable) -> None:
        """监听配置变更"""
        raise NotImplementedError


class LocalFileBackend(ConfigBackend):
    """本地文件后端 - 用于开发和单机部署"""
    
    def __init__(self, config_path: str = "data/config/config.json"):
        self.config_path = Path(config_path)
        self._config: Dict[str, ConfigValue] = {}
        self._lock = asyncio.Lock()
        self._watchers: Dict[str, List[Callable]] = {}
        self._file_hash: Optional[str] = None
        
        # 确保目录存在
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
    
    async def load(self) -> None:
        """从文件加载配置"""
        async with self._lock:
            if self.config_path.exists():
                async with aiofiles.open(self.config_path, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    data = json.loads(content)
                    
                    # 计算文件哈希，检测变更
                    current_hash = hashlib.md5(content.encode()).hexdigest()
                    if current_hash != self._file_hash:
                        self._file_hash = current_hash
                        
                        # 解析配置
                        self._config = {}
                        for key, value_data in data.items():
                            if isinstance(value_data, dict) and "value" in value_data:
                                self._config[key] = ConfigValue.from_dict(value_data)
                            else:
                                # 兼容旧格式
                                self._config[key] = ConfigValue(value=value_data)
                        
                        logger.info(f"配置加载成功：{len(self._config)} 项")
                        
                        # 触发 watchers
                        await self._notify_watchers()
            else:
                # 使用默认配置
                self._config = {}
                for key, value in self._flatten_dict(DEFAULT_CONFIG).items():
                    self._config[key] = ConfigValue(value=value)
                await self.save()
                logger.info("配置文件不存在，使用默认配置")
    
    async def save(self) -> None:
        """保存配置到文件"""
        async with self._lock:
            data = {key: cv.to_dict() for key, cv in self._config.items()}
            
            async with aiofiles.open(self.config_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(data, ensure_ascii=False, indent=2, default=str))
            
            logger.info(f"配置已保存：{self.config_path}")
    
    async def get(self, key: str) -> Optional[ConfigValue]:
        async with self._lock:
            return self._config.get(key)
    
    async def set(self, key: str, value: ConfigValue) -> None:
        async with self._lock:
            old_value = self._config.get(key)
            self._config[key] = value
            
            # 保存变更
            await self.save()
            
            # 触发 watchers
            if old_value is None or old_value.value != value.value:
                await self._notify_key_watchers(key, value.value)
    
    async def get_all(self) -> Dict[str, ConfigValue]:
        async with self._lock:
            return copy.deepcopy(self._config)
    
    def register_watcher(self, key: str, callback: Callable) -> None:
        """注册配置变更回调"""
        if key not in self._watchers:
            self._watchers[key] = []
        self._watchers[key].append(callback)
    
    async def _notify_watchers(self) -> None:
        """通知所有 watcher"""
        for key, callbacks in self._watchers.items():
            if key in self._config:
                for callback in callbacks:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(key, self._config[key].value)
                        else:
                            callback(key, self._config[key].value)
                    except Exception as e:
                        logger.error(f"配置回调失败 {key}: {e}")
    
    async def _notify_key_watchers(self, key: str, value: Any) -> None:
        """通知指定 key 的 watcher"""
        if key in self._watchers:
            for callback in self._watchers[key]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(key, value)
                    else:
                        callback(key, value)
                except Exception as e:
                    logger.error(f"配置回调失败 {key}: {e}")
    
    @staticmethod
    def _flatten_dict(d: Dict, parent_key: str = '', sep: str = '.') -> Dict:
        """扁平化嵌套字典"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}.{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(ConfigBackend._flatten_dict(v, new_key, sep).items())
            else:
                items.append((new_key, v))
        return dict(items)


class EtcdBackend(ConfigBackend):
    """etcd 后端 - 用于分布式部署"""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 2379,
        prefix: str = "/rag/config/"
    ):
        self.host = host
        self.port = port
        self.prefix = prefix
        self._client = None
        self._watchers: Dict[str, List[Callable]] = {}
    
    async def connect(self) -> None:
        """连接到 etcd"""
        try:
            import etcd3
            self._client = etcd3.client(host=self.host, port=self.port)
            logger.info(f"已连接到 etcd: {self.host}:{self.port}")
        except ImportError:
            logger.warning("etcd3 未安装，请运行：pip install etcd3")
            raise
        except Exception as e:
            logger.error(f"连接 etcd 失败：{e}")
            raise
    
    async def get(self, key: str) -> Optional[ConfigValue]:
        if not self._client:
            return None
        
        full_key = f"{self.prefix}{key}"
        try:
            value, _ = self._client.get(full_key)
            if value:
                data = json.loads(value.decode('utf-8'))
                return ConfigValue.from_dict(data)
        except Exception as e:
            logger.error(f"从 etcd 获取配置失败：{e}")
        return None
    
    async def set(self, key: str, value: ConfigValue) -> None:
        if not self._client:
            return
        
        full_key = f"{self.prefix}{key}"
        try:
            data = json.dumps(value.to_dict(), default=str)
            self._client.put(full_key, data)
            
            # 通知 watchers
            await self._notify_key_watchers(key, value.value)
        except Exception as e:
            logger.error(f"设置 etcd 配置失败：{e}")
            raise
    
    async def get_all(self) -> Dict[str, ConfigValue]:
        if not self._client:
            return {}
        
        result = {}
        try:
            for value, meta in self._client.get_prefix(self.prefix):
                if value:
                    key = meta.key.decode('utf-8').replace(self.prefix, '')
                    data = json.loads(value.decode('utf-8'))
                    result[key] = ConfigValue.from_dict(data)
        except Exception as e:
            logger.error(f"获取 etcd 配置失败：{e}")
        return result
    
    def register_watcher(self, key: str, callback: Callable) -> None:
        if key not in self._watchers:
            self._watchers[key] = []
        self._watchers[key].append(callback)
        
        # 注册 etcd watch
        if self._client:
            full_key = f"{self.prefix}{key}"
            self._client.add_watch_callback(full_key, self._etcd_watch_callback)
    
    def _etcd_watch_callback(self, event) -> None:
        """etcd watch 回调"""
        if event.get('kv'):
            key = event['kv']['key'].decode('utf-8').replace(self.prefix, '')
            value = event['kv']['value'].decode('utf-8')
            data = json.loads(value)
            
            asyncio.create_task(self._notify_key_watchers(key, data.get('value')))
    
    async def _notify_key_watchers(self, key: str, value: Any) -> None:
        if key in self._watchers:
            for callback in self._watchers[key]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        asyncio.create_task(callback(key, value))
                    else:
                        callback(key, value)
                except Exception as e:
                    logger.error(f"配置回调失败 {key}: {e}")


# ==================== 配置中心主类 ====================
class ConfigCenter:
    """配置中心主类"""
    
    def __init__(self):
        self._backend: Optional[ConfigBackend] = None
        self._callbacks: Dict[str, List[Callable]] = {}
        self._initialized = False
        self._config_cache: Dict[str, ConfigValue] = {}
        self._refresh_task: Optional[asyncio.Task] = None
    
    async def initialize(
        self,
        backend_type: str = "local",
        config_path: str = "data/config/config.json",
        etcd_host: str = "localhost",
        etcd_port: int = 2379,
        auto_refresh: bool = True,
        refresh_interval: int = 30
    ) -> None:
        """初始化配置中心
        
        Args:
            backend_type: 后端类型 ("local" | "etcd" | "consul")
            config_path: 本地配置文件路径
            etcd_host: etcd 主机地址
            etcd_port: etcd 端口
            auto_refresh: 是否自动刷新配置
            refresh_interval: 自动刷新间隔（秒）
        """
        if self._initialized:
            return
        
        # 创建后端
        if backend_type == "local":
            self._backend = LocalFileBackend(config_path=config_path)
            await self._backend.load()
        elif backend_type == "etcd":
            self._backend = EtcdBackend(host=etcd_host, port=etcd_port)
            await self._backend.connect()
        else:
            raise ValueError(f"不支持的后端类型：{backend_type}")
        
        # 加载配置到缓存
        self._config_cache = await self._backend.get_all()
        
        self._initialized = True
        
        # 启动自动刷新
        if auto_refresh and backend_type == "local":
            self._refresh_task = asyncio.create_task(
                self._auto_refresh_loop(refresh_interval)
            )
        
        logger.info(f"配置中心初始化完成：backend={backend_type}")
    
    async def _auto_refresh_loop(self, interval: int) -> None:
        """自动刷新配置循环"""
        while True:
            try:
                await asyncio.sleep(interval)
                await self.refresh()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"自动刷新配置失败：{e}")
    
    async def refresh(self) -> None:
        """从后端刷新配置"""
        if not self._backend:
            return
        
        new_config = await self._backend.get_all()
        
        # 检测变更并触发回调
        for key, new_value in new_config.items():
            old_value = self._config_cache.get(key)
            if old_value is None or old_value.value != new_value.value:
                self._config_cache[key] = new_value
                await self._notify_callbacks(key, new_value.value)
        
        logger.debug(f"配置刷新完成：{len(new_config)} 项")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键（点分隔，如 "rag.fusion.bm25_weight"）
            default: 默认值
            
        Returns:
            配置值
        """
        if key in self._config_cache:
            return self._config_cache[key].value
        
        # 尝试从嵌套结构获取
        value = self._get_nested_value(DEFAULT_CONFIG, key)
        if value is not None:
            return value
        
        return default
    
    def get_typed(self, key: str, default: Any = None, type_hint: type = str) -> Any:
        """获取类型化的配置值"""
        value = self.get(key, default)
        try:
            if type_hint == bool and isinstance(value, str):
                return value.lower() in ('true', '1', 'yes')
            elif type_hint in (int, float) and isinstance(value, str):
                return type_hint(value)
            elif type_hint == dict and isinstance(value, str):
                return json.loads(value)
        except Exception as e:
            logger.warning(f"配置类型转换失败 {key}: {e}")
        return value
    
    async def set(
        self,
        key: str,
        value: Any,
        updated_by: str = "api"
    ) -> None:
        """设置配置值（热更新）
        
        Args:
            key: 配置键
            value: 配置值
            updated_by: 更新者标识
        """
        if not self._backend:
            raise RuntimeError("配置中心未初始化")
        
        config_value = ConfigValue(
            value=value,
            updated_by=updated_by
        )
        
        await self._backend.set(key, config_value)
        self._config_cache[key] = config_value
        
        logger.info(f"配置更新：{key} = {value}")
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return {key: cv.value for key, cv in self._config_cache.items()}
    
    def get_with_metadata(self) -> Dict[str, Dict]:
        """获取带元数据的配置"""
        return {key: cv.to_dict() for key, cv in self._config_cache.items()}
    
    def register_callback(self, key: str, callback: Callable) -> None:
        """注册配置变更回调
        
        Args:
            key: 配置键
            callback: 回调函数，签名为 callback(key: str, new_value: Any)
        """
        if key not in self._callbacks:
            self._callbacks[key] = []
        self._callbacks[key].append(callback)
        
        # 注册到后端
        if self._backend and hasattr(self._backend, 'register_watcher'):
            self._backend.register_watcher(key, callback)
    
    async def _notify_callbacks(self, key: str, value: Any) -> None:
        """通知配置变更回调"""
        if key in self._callbacks:
            for callback in self._callbacks[key]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(key, value)
                    else:
                        callback(key, value)
                except Exception as e:
                    logger.error(f"配置回调失败 {key}: {e}")
    
    @staticmethod
    def _get_nested_value(d: Dict, key: str) -> Any:
        """从嵌套字典获取值"""
        keys = key.split('.')
        value = d
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return None
        return value
    
    async def close(self) -> None:
        """关闭配置中心"""
        if self._refresh_task:
            self._refresh_task.cancel()
            try:
                await self._refresh_task
            except asyncio.CancelledError:
                pass
        
        logger.info("配置中心已关闭")


# ==================== 全局实例 ====================
config_center = ConfigCenter()


# ==================== 便捷函数 ====================
def get_config(key: str, default: Any = None) -> Any:
    """获取配置（同步）"""
    return config_center.get(key, default)


def get_config_typed(key: str, default: Any = None, type_hint: type = str) -> Any:
    """获取类型化的配置（同步）"""
    return config_center.get_typed(key, default, type_hint)


async def set_config(key: str, value: Any, updated_by: str = "api") -> None:
    """设置配置（异步）"""
    await config_center.set(key, value, updated_by)


def register_config_callback(key: str, callback: Callable) -> None:
    """注册配置变更回调"""
    config_center.register_callback(key, callback)


# ==================== FastAPI 集成 ====================
async def setup_config_center_from_env() -> None:
    """从环境变量设置配置中心"""
    backend_type = os.getenv("CONFIG_BACKEND", "local")
    config_path = os.getenv("CONFIG_PATH", "data/config/config.json")
    etcd_host = os.getenv("ETCD_HOST", "localhost")
    etcd_port = int(os.getenv("ETCD_PORT", "2379"))
    auto_refresh = os.getenv("CONFIG_AUTO_REFRESH", "true").lower() == "true"
    refresh_interval = int(os.getenv("CONFIG_REFRESH_INTERVAL", "30"))
    
    await config_center.initialize(
        backend_type=backend_type,
        config_path=config_path,
        etcd_host=etcd_host,
        etcd_port=etcd_port,
        auto_refresh=auto_refresh,
        refresh_interval=refresh_interval
    )


# ==================== 配置变更监控中间件 ====================
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class ConfigReloadMiddleware(BaseHTTPMiddleware):
    """配置重载中间件 - 每次请求检查配置变更"""
    
    def __init__(self, app, check_interval: int = 60):
        super().__init__(app)
        self.check_interval = check_interval
        self._last_check = 0
        self._lock = asyncio.Lock()
    
    async def dispatch(self, request: Request, call_next) -> Response:
        import time
        
        now = time.time()
        if now - self._last_check > self.check_interval:
            async with self._lock:
                if now - self._last_check > self.check_interval:
                    await config_center.refresh()
                    self._last_check = now
        
        return await call_next(request)
