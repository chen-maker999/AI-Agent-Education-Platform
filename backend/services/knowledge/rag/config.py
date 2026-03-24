"""
RAG 专用配置中心 - P11 优化版

集中管理所有可调参数，支持：
1. 环境变量覆盖
2. JSON 文件加载
3. 配置热更新
4. 配置版本管理

所有 RAG 相关配置统一在此管理，避免硬编码
"""

import json
import os
import threading
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field, asdict
from functools import lru_cache
import hashlib


@dataclass
class RetrievalConfig:
    """检索配置"""
    # 默认返回文档数
    DEFAULT_TOP_K: int = 10
    # 是否启用多样性 (MMR)
    USE_DIVERSITY: bool = True
    # 意图权重配置
    INTENT_WEIGHTS: Dict[str, Dict[str, float]] = field(default_factory=lambda: {
        # 概念解释：侧重语义和关键词
        "concept_explanation": {"semantic": 0.55, "keyword": 0.30, "graph": 0.15},
        # 关系查询：侧重知识图谱
        "relation_query": {"semantic": 0.35, "keyword": 0.20, "graph": 0.45},
        # 代码问题：平衡语义和关键词
        "code_question": {"semantic": 0.50, "keyword": 0.35, "graph": 0.15},
        # 通用问题：平衡所有渠道
        "general": {"semantic": 0.50, "keyword": 0.35, "graph": 0.15},
        # 对比问题：侧重关键词和图谱
        "comparison": {"semantic": 0.40, "keyword": 0.40, "graph": 0.20},
        # 原因解释：侧重语义和图谱
        "why_question": {"semantic": 0.50, "keyword": 0.15, "graph": 0.35},
    })
    # 是否启用 TRR 跨语言检索
    ENABLE_TRR: bool = False
    # 是否启用 Parent-Child 检索
    USE_PARENT_CHILD: bool = False
    # 是否启用 GraphRAG
    USE_GRAPH_RAG: bool = True
    # 是否启用 BM25
    USE_BM25: bool = True
    # 是否启用向量检索
    USE_VECTOR: bool = True
    # 是否启用图谱检索
    USE_GRAPH: bool = True


@dataclass
class CacheConfig:
    """缓存配置"""
    # 查询缓存最大大小
    MAX_SIZE: int = 10000
    # 查询缓存过期时间 (秒)
    TTL: int = 7200
    # 语义缓存相似度阈值
    SEMANTIC_THRESHOLD: float = 0.8
    # 是否启用语义缓存
    ENABLE_SEMANTIC: bool = True
    # 是否启用查询向量缓存
    ENABLE_QUERY_VECTOR: bool = True
    # LRU 淘汰策略
    USE_LRU: bool = True


@dataclass
class RerankConfig:
    """重排序配置"""
    # 重排序模型名称
    MODEL_NAME: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    # 是否启用级联重排序
    USE_CASCADE: bool = True
    # 重排序返回文档数
    TOP_K: int = 10
    # 是否启用重排序
    ENABLED: bool = True
    # 重排序分数阈值
    SCORE_THRESHOLD: float = 0.5


@dataclass
class MMRConfig:
    """MMR (最大边界相关) 配置"""
    # 多样性权重 (0-1)，越大越多样
    LAMBDA: float = 0.5
    # 最大上下文 token 数
    MAX_CONTEXT_TOKENS: int = 3000
    # 是否启用 MMR
    ENABLED: bool = True
    # 上下文压缩比目标
    TARGET_COMPRESSION_RATIO: float = 0.6


@dataclass
class FusionConfig:
    """结果融合配置"""
    # 是否启用 RRF (倒数排名融合)
    USE_RRF: bool = True
    # RRF 参数 k
    RRF_K: int = 60
    # 是否启用加权融合
    USE_WEIGHTED: bool = True
    # 默认权重 (当意图未知时)
    DEFAULT_WEIGHTS: Dict[str, float] = field(default_factory=lambda: {
        "semantic": 0.5,
        "keyword": 0.35,
        "graph": 0.15
    })


@dataclass
class MockLLMConfig:
    """Mock LLM 配置"""
    # 是否启用 Mock LLM 模式
    ENABLED: bool = True
    # Golden Answer 数据库路径
    GOLDEN_DOCS_PATH: str = "evaluation_tools/golden_docs_extended.json"
    # 是否使用模板生成
    USE_TEMPLATE: bool = True
    # 是否使用关键词抽取
    USE_KEYWORD_EXTRACTION: bool = True
    # Mock Embedding 维度
    EMBEDDING_DIM: int = 768


@dataclass
class EvaluationConfig:
    """评估配置"""
    # 评估模式：mock_llm 或 real_llm
    MODE: str = "mock_llm"
    # 测试数据集路径
    DATASET_PATH: str = "evaluation_tools/test_dataset.json"
    # 输出报告路径
    OUTPUT_PATH: str = "evaluation_tools/evaluation_report.json"
    # 最大样本数 (None 表示全部)
    MAX_SAMPLES: Optional[int] = None
    # 是否计算 F1 分数
    CALCULATE_F1: bool = True
    # 指标权重配置
    METRIC_WEIGHTS: Dict[str, float] = field(default_factory=lambda: {
        "faithfulness": 0.2,
        "answer_relevancy": 0.2,
        "context_precision": 0.2,
        "context_recall": 0.2,
        "answer_correctness": 0.2
    })


@dataclass
class MonitoringConfig:
    """监控配置"""
    # 是否启用 Prometheus
    ENABLE_PROMETHEUS: bool = True
    # 指标采集间隔 (秒)
    METRICS_INTERVAL: int = 60
    # 是否启用性能追踪
    ENABLE_PERFORMANCE_TRACKING: bool = True
    # 延迟告警阈值 (ms)
    LATENCY_ALERT_THRESHOLD_MS: int = 100
    # 错误率告警阈值 (%)
    ERROR_RATE_ALERT_THRESHOLD: float = 0.05
    # 缓存命中率告警阈值 (%)
    CACHE_HIT_RATE_ALERT_THRESHOLD: float = 0.2


@dataclass
class StaticIndexConfig:
    """静态索引配置"""
    # 是否启用静态库
    ENABLED: bool = True
    # 静态库路径
    INDEX_PATH: str = "data/static_index"
    # 是否启用增量更新
    INCREMENTAL_UPDATE: bool = True
    # 定期全量重建间隔 (小时)
    REBUILD_INTERVAL_HOURS: int = 24
    # 版本号
    VERSION: int = 1


class RAGConfig:
    """
    RAG 配置中心
    
    单例模式，全局访问
    """

    _instance: Optional['RAGConfig'] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._config_dir = Path(__file__).parent.parent.parent / "config"
        self._config_file = self._config_dir / "rag_config.json"
        self._watchers: List[Callable[[str, Any, Any], None]] = []
        self._last_modified: Optional[float] = None
        self._config_hash: Optional[str] = None

        # 加载配置
        self.retrieval = RetrievalConfig()
        self.cache = CacheConfig()
        self.rerank = RerankConfig()
        self.mmr = MMRConfig()
        self.fusion = FusionConfig()
        self.mock_llm = MockLLMConfig()
        self.evaluation = EvaluationConfig()
        self.monitoring = MonitoringConfig()
        self.static_index = StaticIndexConfig()

        # 从环境变量加载
        self._load_from_env()

        # 从 JSON 文件加载 (如果存在)
        self._load_from_file()

        self._initialized = True

    def _load_from_env(self):
        """从环境变量加载配置"""
        # Retrieval
        if os.getenv('RAG_DEFAULT_TOP_K'):
            self.retrieval.DEFAULT_TOP_K = int(os.getenv('RAG_DEFAULT_TOP_K'))
        if os.getenv('RAG_ENABLE_TRR'):
            self.retrieval.ENABLE_TRR = os.getenv('RAG_ENABLE_TRR').lower() == 'true'
        if os.getenv('RAG_USE_BM25'):
            self.retrieval.USE_BM25 = os.getenv('RAG_USE_BM25').lower() == 'true'
        if os.getenv('RAG_USE_VECTOR'):
            self.retrieval.USE_VECTOR = os.getenv('RAG_USE_VECTOR').lower() == 'true'

        # Cache
        if os.getenv('RAG_CACHE_MAX_SIZE'):
            self.cache.MAX_SIZE = int(os.getenv('RAG_CACHE_MAX_SIZE'))
        if os.getenv('RAG_CACHE_TTL'):
            self.cache.TTL = int(os.getenv('RAG_CACHE_TTL'))
        if os.getenv('RAG_SEMANTIC_CACHE_THRESHOLD'):
            self.cache.SEMANTIC_THRESHOLD = float(os.getenv('RAG_SEMANTIC_CACHE_THRESHOLD'))

        # Rerank
        if os.getenv('RAG_RERANK_MODEL_NAME'):
            self.rerank.MODEL_NAME = os.getenv('RAG_RERANK_MODEL_NAME')
        if os.getenv('RAG_ENABLE_RERANK'):
            self.rerank.ENABLED = os.getenv('RAG_ENABLE_RERANK').lower() == 'true'

        # MMR
        if os.getenv('RAG_MMR_LAMBDA'):
            self.mmr.LAMBDA = float(os.getenv('RAG_MMR_LAMBDA'))
        if os.getenv('RAG_MAX_CONTEXT_TOKENS'):
            self.mmr.MAX_CONTEXT_TOKENS = int(os.getenv('RAG_MAX_CONTEXT_TOKENS'))

        # Mock LLM
        if os.getenv('RAG_MOCK_LLM_ENABLED'):
            self.mock_llm.ENABLED = os.getenv('RAG_MOCK_LLM_ENABLED').lower() == 'true'

        # Evaluation
        if os.getenv('RAG_EVALUATION_MODE'):
            self.evaluation.MODE = os.getenv('RAG_EVALUATION_MODE')

        # Monitoring
        if os.getenv('RAG_ENABLE_PROMETHEUS'):
            self.monitoring.ENABLE_PROMETHEUS = os.getenv('RAG_ENABLE_PROMETHEUS').lower() == 'true'

    def _load_from_file(self):
        """从 JSON 文件加载配置"""
        if not self._config_file.exists():
            return

        try:
            with open(self._config_file, 'r', encoding='utf-8') as f:
                file_config = json.load(f)

            # 更新各配置项
            if 'retrieval' in file_config:
                self._update_dataclass(self.retrieval, file_config['retrieval'])
            if 'cache' in file_config:
                self._update_dataclass(self.cache, file_config['cache'])
            if 'rerank' in file_config:
                self._update_dataclass(self.rerank, file_config['rerank'])
            if 'mmr' in file_config:
                self._update_dataclass(self.mmr, file_config['mmr'])
            if 'fusion' in file_config:
                self._update_dataclass(self.fusion, file_config['fusion'])
            if 'mock_llm' in file_config:
                self._update_dataclass(self.mock_llm, file_config['mock_llm'])
            if 'evaluation' in file_config:
                self._update_dataclass(self.evaluation, file_config['evaluation'])
            if 'monitoring' in file_config:
                self._update_dataclass(self.monitoring, file_config['monitoring'])
            if 'static_index' in file_config:
                self._update_dataclass(self.static_index, file_config['static_index'])

            self._last_modified = self._config_file.stat().st_mtime
            self._config_hash = self._compute_config_hash()

        except Exception as e:
            print(f"[RAGConfig] 加载配置文件失败：{e}")

    def _update_dataclass(self, config_obj: Any, updates: Dict[str, Any]):
        """更新 dataclass 配置"""
        for key, value in updates.items():
            if hasattr(config_obj, key):
                setattr(config_obj, key, value)

    def _compute_config_hash(self) -> str:
        """计算配置哈希值，用于检测变化"""
        config_dict = self.to_dict()
        config_str = json.dumps(config_dict, sort_keys=True)
        return hashlib.md5(config_str.encode('utf-8')).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """将配置转换为字典"""
        return {
            'retrieval': asdict(self.retrieval),
            'cache': asdict(self.cache),
            'rerank': asdict(self.rerank),
            'mmr': asdict(self.mmr),
            'fusion': asdict(self.fusion),
            'mock_llm': asdict(self.mock_llm),
            'evaluation': asdict(self.evaluation),
            'monitoring': asdict(self.monitoring),
            'static_index': asdict(self.static_index)
        }

    def save_to_file(self, path: Optional[str] = None):
        """保存配置到文件"""
        config_path = Path(path) if path else self._config_file
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

        print(f"[RAGConfig] 配置已保存：{config_path}")
        self._last_modified = config_path.stat().st_mtime
        self._config_hash = self._compute_config_hash()

    def reload(self):
        """重新加载配置"""
        self._load_from_env()
        self._load_from_file()
        print("[RAGConfig] 配置已重新加载")

    def register_watcher(self, callback: Callable[[str, Any, Any], None]):
        """
        注册配置变更监听器

        Args:
            callback: 回调函数 (config_key, old_value, new_value)
        """
        self._watchers.append(callback)

    def update(self, key: str, value: Any):
        """
        更新配置项

        Args:
            key: 配置键 (点号分隔，如 'retrieval.DEFAULT_TOP_K')
            value: 新值
        """
        keys = key.split('.')
        if len(keys) != 2:
            raise ValueError(f"无效的配置键：{key}")

        section, param = keys
        section_obj = getattr(self, section, None)

        if section_obj is None:
            raise ValueError(f"无效的配置段：{section}")

        if not hasattr(section_obj, param):
            raise ValueError(f"无效的配置项：{key}")

        old_value = getattr(section_obj, param)
        setattr(section_obj, param, value)

        # 通知监听器
        for watcher in self._watchers:
            watcher(key, old_value, value)

        print(f"[RAGConfig] 配置更新：{key} = {value}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项

        Args:
            key: 配置键 (点号分隔)
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split('.')
        if len(keys) != 2:
            return default

        section, param = keys
        section_obj = getattr(self, section, None)

        if section_obj is None:
            return default

        return getattr(section_obj, param, default)

    def check_for_changes(self) -> bool:
        """检查配置文件是否有变化"""
        if not self._config_file.exists():
            return False

        current_mtime = self._config_file.stat().st_mtime
        if current_mtime != self._last_modified:
            print("[RAGConfig] 检测到配置文件变化，重新加载...")
            self.reload()
            return True
        return False

    def start_auto_reload(self, interval: int = 60):
        """
        启动自动重载

        Args:
            interval: 检查间隔 (秒)
        """
        def check_changes():
            while True:
                time.sleep(interval)
                self.check_for_changes()

        thread = threading.Thread(target=check_changes, daemon=True)
        thread.start()
        print(f"[RAGConfig] 自动重载已启动 (间隔：{interval}秒)")


# 全局单例
_config_instance: Optional[RAGConfig] = None


def get_config() -> RAGConfig:
    """获取配置中心单例"""
    global _config_instance
    if _config_instance is None:
        _config_instance = RAGConfig()
    return _config_instance


# 便捷访问函数
def get_retrieval_config() -> RetrievalConfig:
    """获取检索配置"""
    return get_config().retrieval


def get_cache_config() -> CacheConfig:
    """获取缓存配置"""
    return get_config().cache


def get_rerank_config() -> RerankConfig:
    """获取重排序配置"""
    return get_config().rerank


def get_mmr_config() -> MMRConfig:
    """获取 MMR 配置"""
    return get_config().mmr


def get_fusion_config() -> FusionConfig:
    """获取融合配置"""
    return get_config().fusion


def get_mock_llm_config() -> MockLLMConfig:
    """获取 Mock LLM 配置"""
    return get_config().mock_llm


def get_evaluation_config() -> EvaluationConfig:
    """获取评估配置"""
    return get_config().evaluation


def get_monitoring_config() -> MonitoringConfig:
    """获取监控配置"""
    return get_config().monitoring


def get_static_index_config() -> StaticIndexConfig:
    """获取静态索引配置"""
    return get_config().static_index


# 测试代码
if __name__ == "__main__":
    config = get_config()

    print("=" * 60)
    print("RAG 配置中心")
    print("=" * 60)

    print("\n检索配置:")
    print(f"  DEFAULT_TOP_K: {config.retrieval.DEFAULT_TOP_K}")
    print(f"  ENABLE_TRR: {config.retrieval.ENABLE_TRR}")
    print(f"  USE_BM25: {config.retrieval.USE_BM25}")

    print("\n缓存配置:")
    print(f"  MAX_SIZE: {config.cache.MAX_SIZE}")
    print(f"  TTL: {config.cache.TTL}")
    print(f"  SEMANTIC_THRESHOLD: {config.cache.SEMANTIC_THRESHOLD}")

    print("\n重排序配置:")
    print(f"  MODEL_NAME: {config.rerank.MODEL_NAME}")
    print(f"  ENABLED: {config.rerank.ENABLED}")

    print("\nMMR 配置:")
    print(f"  LAMBDA: {config.mmr.LAMBDA}")
    print(f"  MAX_CONTEXT_TOKENS: {config.mmr.MAX_CONTEXT_TOKENS}")

    print("\nMock LLM 配置:")
    print(f"  ENABLED: {config.mock_llm.ENABLED}")
    print(f"  GOLDEN_DOCS_PATH: {config.mock_llm.GOLDEN_DOCS_PATH}")

    print("\n评估配置:")
    print(f"  MODE: {config.evaluation.MODE}")
    print(f"  DATASET_PATH: {config.evaluation.DATASET_PATH}")

    print("\n监控配置:")
    print(f"  ENABLE_PROMETHEUS: {config.monitoring.ENABLE_PROMETHEUS}")
    print(f"  LATENCY_ALERT_THRESHOLD_MS: {config.monitoring.LATENCY_ALERT_THRESHOLD_MS}")

    # 测试配置更新
    print("\n" + "=" * 60)
    print("测试配置更新")
    print("=" * 60)

    def on_config_change(key: str, old_value: Any, new_value: Any):
        print(f"配置变更：{key} 从 {old_value} 变为 {new_value}")

    config.register_watcher(on_config_change)
    config.update('retrieval.DEFAULT_TOP_K', 15)
    config.update('cache.MAX_SIZE', 20000)

    # 保存配置
    config.save_to_file()

    print("\n配置字典:")
    print(json.dumps(config.to_dict(), ensure_ascii=False, indent=2)[:1000] + "...")
