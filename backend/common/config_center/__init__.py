"""配置中心模块 - P3-001

提供统一的配置管理，支持热更新和多种后端存储。
"""

from .main import (
    config_center,
    ConfigCenter,
    ConfigBackend,
    LocalFileBackend,
    EtcdBackend,
    ConfigValue,
    DEFAULT_CONFIG,
    get_config,
    get_config_typed,
    set_config,
    register_config_callback,
    setup_config_center_from_env,
    ConfigReloadMiddleware,
)

__all__ = [
    "config_center",
    "ConfigCenter",
    "ConfigBackend",
    "LocalFileBackend",
    "EtcdBackend",
    "ConfigValue",
    "DEFAULT_CONFIG",
    "get_config",
    "get_config_typed",
    "set_config",
    "register_config_callback",
    "setup_config_center_from_env",
    "ConfigReloadMiddleware",
]
