"""配置热更新示例 - P3-001

演示如何使用配置中心实现 RAG 参数的热更新。
"""

import asyncio
from typing import Any
from datetime import datetime

try:
    from common.config_center import config_center, register_config_callback, get_config
    from common.logging_config import get_context_logger
    logger = get_context_logger("config_hot_reload")
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


# ==================== 配置变更处理器 ====================
class ConfigChangeHandler:
    """配置变更处理器"""
    
    def __init__(self):
        self._last_update = None
        self._update_count = 0
    
    async def on_fusion_weight_change(self, key: str, new_value: Any):
        """融合权重变更处理"""
        self._last_update = datetime.utcnow()
        self._update_count += 1
        
        logger.info(
            f"融合权重更新：{key} = {new_value}",
            extra={
                "config_key": key,
                "old_value": get_config(key),
                "new_value": new_value,
                "update_count": self._update_count,
            }
        )
        
        # TODO: 通知 RAG 服务重新加载权重
        # 可以通过事件总线或直接调用
    
    async def on_rrf_k_change(self, key: str, new_value: Any):
        """RRF 参数 k 变更处理"""
        logger.info(f"RRF 参数更新：{key} = {new_value}")
        
        # TODO: 重新初始化融合服务
    
    async def on_cache_ttl_change(self, key: str, new_value: Any):
        """缓存 TTL 变更处理"""
        logger.info(f"缓存 TTL 更新：{key} = {new_value} 秒")
        
        # TODO: 更新缓存配置
    
    async def on_rate_limit_change(self, key: str, new_value: Any):
        """限流配置变更处理"""
        logger.info(f"限流配置更新：{key} = {new_value}")
        
        # TODO: 更新限流中间件配置
    
    async def on_kimi_timeout_change(self, key: str, new_value: Any):
        """Kimi API 超时变更处理"""
        logger.info(f"Kimi API 超时更新：{key} = {new_value} 秒")
        
        # TODO: 更新 Kimi 客户端配置


# 全局处理器实例
config_handler = ConfigChangeHandler()


# ==================== 注册回调 ====================
def register_rag_config_callbacks():
    """注册 RAG 配置变更回调"""
    
    # 融合权重回调
    register_config_callback("rag.fusion.semantic_weight", config_handler.on_fusion_weight_change)
    register_config_callback("rag.fusion.keyword_weight", config_handler.on_fusion_weight_change)
    register_config_callback("rag.fusion.graph_weight", config_handler.on_fusion_weight_change)
    
    # RRF 参数回调
    register_config_callback("rag.fusion.rrf_k", config_handler.on_rrf_k_change)
    
    # 缓存配置回调
    register_config_callback("rag.cache.ttl_seconds", config_handler.on_cache_ttl_change)
    
    # 限流配置回调
    register_config_callback("rate_limit.default_requests", config_handler.on_rate_limit_change)
    register_config_callback("rate_limit.bucket_capacity", config_handler.on_rate_limit_change)
    
    # Kimi API 配置回调
    register_config_callback("kimi.timeout", config_handler.on_kimi_timeout_change)
    register_config_callback("kimi.max_retries", config_handler.on_kimi_timeout_change)
    
    logger.info("RAG 配置变更回调已注册")


# ==================== 配置读取示例 ====================
def get_rag_fusion_weights():
    """获取 RAG 融合权重（从配置中心）"""
    return {
        "semantic": get_config("rag.fusion.semantic_weight", 0.4),
        "keyword": get_config("rag.fusion.keyword_weight", 0.3),
        "graph": get_config("rag.fusion.graph_weight", 0.3),
    }


def get_rag_retrieval_config():
    """获取 RAG 检索配置"""
    return {
        "top_k": get_config("rag.retrieval.top_k", 10),
        "timeout_seconds": get_config("rag.retrieval.timeout_seconds", 5),
        "use_rerank": get_config("rag.retrieval.use_rerank", True),
        "use_rewrite": get_config("rag.retrieval.use_rewrite", True),
    }


def get_rag_context_config():
    """获取 RAG 上下文配置"""
    return {
        "max_tokens": get_config("rag.context.max_tokens", 3000),
        "use_diversity": get_config("rag.context.use_diversity", True),
        "mmr_lambda": get_config("rag.context.mmr_lambda", 0.5),
    }


# ==================== 使用示例 ====================
async def demo_hot_reload():
    """演示配置热更新"""
    from common.config_center import setup_config_center_from_env, set_config
    
    # 初始化配置中心
    await setup_config_center_from_env()
    
    # 注册回调
    register_rag_config_callbacks()
    
    # 读取当前配置
    print("\n=== 当前配置 ===")
    print(f"语义权重：{get_config('rag.fusion.semantic_weight')}")
    print(f"关键词权重：{get_config('rag.fusion.keyword_weight')}")
    print(f"图谱权重：{get_config('rag.fusion.graph_weight')}")
    print(f"RRF k 值：{get_config('rag.fusion.rrf_k')}")
    
    # 更新配置（热更新）
    print("\n=== 更新配置 ===")
    await set_config("rag.fusion.semantic_weight", 0.5, updated_by="demo")
    await set_config("rag.fusion.keyword_weight", 0.25, updated_by="demo")
    await set_config("rag.fusion.graph_weight", 0.25, updated_by="demo")
    await set_config("rag.fusion.rrf_k", 50, updated_by="demo")
    
    # 等待回调执行
    await asyncio.sleep(0.5)
    
    # 再次读取配置
    print("\n=== 更新后配置 ===")
    print(f"语义权重：{get_config('rag.fusion.semantic_weight')}")
    print(f"关键词权重：{get_config('rag.fusion.keyword_weight')}")
    print(f"图谱权重：{get_config('rag.fusion.graph_weight')}")
    print(f"RRF k 值：{get_config('rag.fusion.rrf_k')}")
    
    # 获取完整配置
    print("\n=== 完整配置 ===")
    all_configs = config_center.get_all()
    for key, value in sorted(all_configs.items()):
        print(f"  {key}: {value}")
    
    # 关闭配置中心
    await config_center.close()


if __name__ == "__main__":
    asyncio.run(demo_hot_reload())
