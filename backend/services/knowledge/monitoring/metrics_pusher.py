"""监控指标推送服务 (P3-002) - 将内部指标推送到 Prometheus"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime
import threading
import time
import asyncio
from functools import wraps

try:
    from prometheus_client import CollectorRegistry
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    print("[Monitoring Push] Prometheus 未安装，请运行：pip install prometheus-client")

router = APIRouter(prefix="/metrics", tags=["Metrics Push"])

# ==================== 数据结构 ====================
class MetricRecord(BaseModel):
    """指标记录"""
    name: str
    value: float
    labels: Optional[Dict[str, str]] = None
    timestamp: Optional[float] = None
    metric_type: str = "gauge"  # gauge, counter, histogram


class MetricsBatch(BaseModel):
    """批量指标"""
    metrics: List[MetricRecord]


# ==================== 指标推送器 ====================
class MetricsPusher:
    """指标推送器 - 将内部指标推送到 Prometheus"""

    def __init__(self):
        self._registry = CollectorRegistry() if PROMETHEUS_AVAILABLE else None
        self._gauges: Dict[str, Any] = {}
        self._counters: Dict[str, Any] = {}
        self._histograms: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._running = False
        self._push_task: Optional[asyncio.Task] = None
        self._push_interval = 15  # 默认 15 秒推送一次

    def register_gauge(self, name: str, description: str, labels: Optional[List[str]] = None):
        """注册 Gauge 指标"""
        if not PROMETHEUS_AVAILABLE:
            return

        from prometheus_client import Gauge

        with self._lock:
            if name not in self._gauges:
                self._gauges[name] = Gauge(
                    name,
                    description,
                    labelnames=labels or [],
                    registry=self._registry
                )

    def register_counter(self, name: str, description: str, labels: Optional[List[str]] = None):
        """注册 Counter 指标"""
        if not PROMETHEUS_AVAILABLE:
            return

        from prometheus_client import Counter

        with self._lock:
            if name not in self._counters:
                self._counters[name] = Counter(
                    name,
                    description,
                    labelnames=labels or [],
                    registry=self._registry
                )

    def register_histogram(self, name: str, description: str, buckets: Optional[List[float]] = None, labels: Optional[List[str]] = None):
        """注册 Histogram 指标"""
        if not PROMETHEUS_AVAILABLE:
            return

        from prometheus_client import Histogram

        with self._lock:
            if name not in self._histograms:
                self._histograms[name] = Histogram(
                    name,
                    description,
                    buckets=buckets or Histogram.DEFAULT_BUCKETS,
                    labelnames=labels or [],
                    registry=self._registry
                )

    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """设置 Gauge 值"""
        if not PROMETHEUS_AVAILABLE:
            return

        if name not in self._gauges:
            self.register_gauge(name, f"Auto-registered gauge: {name}")

        gauge = self._gauges[name]
        if labels:
            gauge.labels(**labels).set(value)
        else:
            gauge.set(value)

    def inc_counter(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """增加 Counter 值"""
        if not PROMETHEUS_AVAILABLE:
            return

        if name not in self._counters:
            self.register_counter(name, f"Auto-registered counter: {name}")

        counter = self._counters[name]
        if labels:
            counter.labels(**labels).inc(value)
        else:
            counter.inc(value)

    def observe_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """记录 Histogram 观察值"""
        if not PROMETHEUS_AVAILABLE:
            return

        if name not in self._histograms:
            self.register_histogram(name, f"Auto-registered histogram: {name}")

        histogram = self._histograms[name]
        if labels:
            histogram.labels(**labels).observe(value)
        else:
            histogram.observe(value)

    def push_metrics(self, metrics: List[MetricRecord]):
        """批量推送指标"""
        for metric in metrics:
            if metric.metric_type == "gauge":
                self.set_gauge(metric.name, metric.value, metric.labels)
            elif metric.metric_type == "counter":
                self.inc_counter(metric.name, metric.value, metric.labels)
            elif metric.metric_type == "histogram":
                self.observe_histogram(metric.name, metric.value, metric.labels)

    def get_registry(self):
        """获取注册表"""
        return self._registry


# 全局指标推送器
metrics_pusher = MetricsPusher()


# ==================== 预定义指标注册 ====================
def register_rag_metrics():
    """注册 RAG 系统关键指标"""
    if not PROMETHEUS_AVAILABLE:
        return

    # 检索性能指标
    metrics_pusher.register_histogram(
        "rag_retrieval_duration_seconds",
        "RAG 检索耗时",
        buckets=(0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0),
        labels=["method"]  # semantic, keyword, graph
    )

    metrics_pusher.register_gauge(
        "rag_retrieval_results_count",
        "检索结果数量",
        labels=["method"]
    )

    # 融合性能指标
    metrics_pusher.register_histogram(
        "rag_fusion_duration_seconds",
        "RAG 融合耗时",
        buckets=(0.01, 0.02, 0.05, 0.1, 0.2),
        labels=["algorithm"]  # rrf, weighted
    )

    # 重排序指标
    metrics_pusher.register_histogram(
        "rag_rerank_duration_seconds",
        "RAG 重排序耗时",
        buckets=(0.01, 0.02, 0.05, 0.1, 0.2, 0.5)
    )

    metrics_pusher.register_gauge(
        "rag_rerank_score",
        "重排序分数",
        labels=["model"]
    )

    # 缓存指标
    metrics_pusher.register_counter(
        "rag_cache_hits_total",
        "缓存命中总数",
        labels=["cache_level"]  # l1, l2, redis
    )

    metrics_pusher.register_counter(
        "rag_cache_misses_total",
        "缓存未命中总数"
    )

    metrics_pusher.register_gauge(
        "rag_cache_size",
        "缓存大小",
        labels=["cache_level"]
    )

    metrics_pusher.register_gauge(
        "rag_cache_hit_ratio",
        "缓存命中率"
    )

    # LLM 生成指标
    metrics_pusher.register_histogram(
        "rag_llm_generation_duration_seconds",
        "LLM 生成耗时",
        buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0)
    )

    metrics_pusher.register_histogram(
        "rag_llm_tokens_generated",
        "LLM 生成的 token 数",
        buckets=(50, 100, 200, 500, 1000, 2000, 5000)
    )

    # 意图识别指标
    metrics_pusher.register_histogram(
        "rag_intent_classification_duration_seconds",
        "意图识别耗时",
        buckets=(0.001, 0.005, 0.01, 0.02, 0.05, 0.1)
    )

    metrics_pusher.register_gauge(
        "rag_intent_confidence",
        "意图识别置信度",
        labels=["intent"]
    )

    # 知识图谱指标
    metrics_pusher.register_histogram(
        "rag_graph_search_duration_seconds",
        "图谱检索耗时",
        buckets=(0.01, 0.05, 0.1, 0.2, 0.5, 1.0)
    )

    metrics_pusher.register_gauge(
        "rag_graph_entities_found",
        "图谱找到的实体数"
    )

    # 系统健康指标
    metrics_pusher.register_gauge(
        "rag_system_health_status",
        "系统健康状态 (1=healthy, 0=unhealthy)"
    )

    metrics_pusher.register_gauge(
        "rag_active_requests",
        "活跃请求数"
    )

    metrics_pusher.register_gauge(
        "rag_queue_size",
        "请求队列大小"
    )


# ==================== 性能追踪上下文 ====================
class MetricsContext:
    """性能追踪上下文管理器"""

    def __init__(self, metric_name: str, labels: Optional[Dict[str, str]] = None):
        self.metric_name = metric_name
        self.labels = labels or {}
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        metrics_pusher.observe_histogram(self.metric_name, duration, self.labels)
        return False


def track_metrics(metric_name: str, labels: Optional[Dict[str, str]] = None):
    """性能追踪装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                metrics_pusher.observe_histogram(metric_name, duration, labels)

        return wrapper
    return decorator


# ==================== API 接口 ====================
@router.post("/push")
async def push_metrics(metrics: MetricsBatch):
    """推送批量指标"""
    metrics_pusher.push_metrics(metrics.metrics)
    return {
        "code": 200,
        "message": f"成功推送 {len(metrics.metrics)} 条指标"
    }


@router.post("/push/gauge")
async def push_gauge_metric(
    name: str,
    value: float,
    labels: Optional[Dict[str, str]] = None
):
    """推送 Gauge 指标"""
    metrics_pusher.set_gauge(name, value, labels)
    return {"code": 200, "message": "推送成功"}


@router.post("/push/counter")
async def push_counter_metric(
    name: str,
    value: float = 1.0,
    labels: Optional[Dict[str, str]] = None
):
    """推送 Counter 指标"""
    metrics_pusher.inc_counter(name, value, labels)
    return {"code": 200, "message": "推送成功"}


@router.post("/push/histogram")
async def push_histogram_metric(
    name: str,
    value: float,
    labels: Optional[Dict[str, str]] = None
):
    """推送 Histogram 指标"""
    metrics_pusher.observe_histogram(name, value, labels)
    return {"code": 200, "message": "推送成功"}


@router.get("/status")
async def get_pusher_status():
    """获取推送器状态"""
    return {
        "code": 200,
        "data": {
            "prometheus_available": PROMETHEUS_AVAILABLE,
            "running": metrics_pusher._running,
            "push_interval": metrics_pusher._push_interval,
            "registered_gauges": len(metrics_pusher._gauges),
            "registered_counters": len(metrics_pusher._counters),
            "registered_histograms": len(metrics_pusher._histograms)
        }
    }


# ==================== 初始化 ====================
def init_metrics_pusher():
    """初始化指标推送器"""
    register_rag_metrics()
    print("[Monitoring Push] RAG 指标注册完成")


# 自动初始化
init_metrics_pusher()
