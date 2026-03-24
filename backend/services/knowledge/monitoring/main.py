"""性能监控服务 (MONITORING) - Prometheus 指标 + 性能追踪"""

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime
import time
from functools import wraps
import threading
import json

try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST, CollectorRegistry
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    print("[Monitoring] Prometheus 未安装，请运行：pip install prometheus-client")

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])

# ==================== Prometheus 指标定义 ====================
if PROMETHEUS_AVAILABLE:
    # 创建自定义注册表
    registry = CollectorRegistry()
    
    # RAG 检索指标
    RAG_REQUEST_TOTAL = Counter(
        'rag_requests_total',
        'RAG 请求总数',
        ['status', 'intent'],
        registry=registry
    )
    
    RAG_REQUEST_LATENCY = Histogram(
        'rag_request_latency_seconds',
        'RAG 请求延迟',
        ['endpoint'],
        buckets=(0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0),
        registry=registry
    )
    
    # 检索性能指标
    RETRIEVAL_LATENCY = Histogram(
        'retrieval_latency_seconds',
        '检索延迟',
        ['method'],  # semantic, keyword, graph
        buckets=(0.01, 0.02, 0.05, 0.1, 0.2, 0.5),
        registry=registry
    )
    
    RETRIEVAL_RESULTS_COUNT = Histogram(
        'retrieval_results_count',
        '检索结果数量',
        ['method'],
        buckets=(1, 2, 5, 10, 20, 50, 100),
        registry=registry
    )
    
    # 融合性能指标
    FUSION_LATENCY = Histogram(
        'fusion_latency_seconds',
        '结果融合延迟',
        ['method'],  # rrf, weighted
        buckets=(0.01, 0.02, 0.05, 0.1, 0.2),
        registry=registry
    )
    
    FUSION_INPUT_COUNT = Gauge(
        'fusion_input_count',
        '融合输入文档数量',
        registry=registry
    )
    
    # 重排序指标
    RERANK_LATENCY = Histogram(
        'rerank_latency_seconds',
        '重排序延迟',
        buckets=(0.01, 0.02, 0.05, 0.1, 0.2, 0.5),
        registry=registry
    )
    
    # 缓存指标
    CACHE_HIT_TOTAL = Counter(
        'cache_hits_total',
        '缓存命中总数',
        ['cache_level'],  # l1, l2
        registry=registry
    )
    
    CACHE_MISS_TOTAL = Counter(
        'cache_misses_total',
        '缓存未命中总数',
        registry=registry
    )
    
    CACHE_SIZE = Gauge(
        'cache_size',
        '缓存大小',
        ['cache_level'],
        registry=registry
    )
    
    # 上下文压缩指标
    CONTEXT_COMPRESSION_RATIO = Gauge(
        'context_compression_ratio',
        '上下文压缩比',
        registry=registry
    )
    
    CONTEXT_TOKENS = Histogram(
        'context_tokens',
        '上下文 token 数量',
        buckets=(100, 500, 1000, 2000, 3000, 5000, 10000),
        registry=registry
    )
    
    # LLM 生成指标
    LLM_GENERATION_LATENCY = Histogram(
        'llm_generation_latency_seconds',
        'LLM 生成延迟',
        buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 20.0),
        registry=registry
    )
    
    LLM_TOKENS_GENERATED = Histogram(
        'llm_tokens_generated',
        'LLM 生成的 token 数',
        buckets=(50, 100, 200, 500, 1000, 2000),
        registry=registry
    )
    
    # 系统资源指标
    ACTIVE_CONNECTIONS = Gauge(
        'active_connections',
        '活跃连接数',
        registry=registry
    )
    
    ERROR_TOTAL = Counter(
        'errors_total',
        '错误总数',
        ['service', 'error_type'],
        registry=registry
    )


# ==================== 性能追踪器 ====================
class PerformanceTracker:
    """性能追踪器"""
    
    def __init__(self):
        self._metrics: Dict[str, List[float]] = {}
        self._lock = threading.Lock()
        self._stats = {
            "total_requests": 0,
            "total_errors": 0,
            "start_time": datetime.utcnow()
        }
    
    def record_latency(self, metric_name: str, latency: float):
        """记录延迟"""
        with self._lock:
            if metric_name not in self._metrics:
                self._metrics[metric_name] = []
            self._metrics[metric_name].append(latency)
            
            # 只保留最近 1000 条记录
            if len(self._metrics[metric_name]) > 1000:
                self._metrics[metric_name] = self._metrics[metric_name][-1000:]
    
    def record_count(self, metric_name: str, count: int):
        """记录数量"""
        self.record_latency(metric_name, float(count))
    
    def get_percentile(self, metric_name: str, percentile: float) -> Optional[float]:
        """获取百分位数"""
        with self._lock:
            if metric_name not in self._metrics or not self._metrics[metric_name]:
                return None
            
            sorted_values = sorted(self._metrics[metric_name])
            index = int(len(sorted_values) * percentile / 100)
            return sorted_values[min(index, len(sorted_values) - 1)]
    
    def get_stats(self, metric_name: str) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            if metric_name not in self._metrics or not self._metrics[metric_name]:
                return {}
            
            values = self._metrics[metric_name]
            return {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "p50": self.get_percentile(metric_name, 50),
                "p95": self.get_percentile(metric_name, 95),
                "p99": self.get_percentile(metric_name, 99)
            }
    
    def increment_request(self):
        """增加请求计数"""
        self._stats["total_requests"] += 1
    
    def increment_error(self):
        """增加错误计数"""
        self._stats["total_errors"] += 1
    
    def get_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        uptime = (datetime.utcnow() - self._stats["start_time"]).total_seconds()
        
        return {
            **self._stats,
            "uptime_seconds": uptime,
            "requests_per_second": self._stats["total_requests"] / max(uptime, 1),
            "error_rate": self._stats["total_errors"] / max(self._stats["total_requests"], 1)
        }


# 全局性能追踪器
performance_tracker = PerformanceTracker()


# ==================== 性能监控装饰器 ====================
def monitor_performance(endpoint_name: str):
    """性能监控装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            performance_tracker.increment_request()
            
            try:
                result = await func(*args, **kwargs)
                
                # 记录成功
                if PROMETHEUS_AVAILABLE:
                    RAG_REQUEST_TOTAL.labels(status='success', intent='general').inc()
                
                return result
                
            except Exception as e:
                # 记录错误
                performance_tracker.increment_error()
                if PROMETHEUS_AVAILABLE:
                    ERROR_TOTAL.labels(service='rag', error_type=type(e).__name__).inc()
                raise
                
            finally:
                # 记录延迟
                latency = time.time() - start_time
                performance_tracker.record_latency(endpoint_name, latency)
                
                if PROMETHEUS_AVAILABLE:
                    RAG_REQUEST_LATENCY.labels(endpoint=endpoint_name).observe(latency)
        
        return wrapper
    return decorator


# ==================== 性能分析上下文管理器 ====================
class PerformanceContext:
    """性能分析上下文"""
    
    def __init__(self, metric_name: str, labels: Optional[Dict[str, str]] = None):
        self.metric_name = metric_name
        self.labels = labels or {}
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        latency = time.time() - self.start_time
        performance_tracker.record_latency(self.metric_name, latency)
        
        if PROMETHEUS_AVAILABLE:
            if self.metric_name == 'retrieval':
                RETRIEVAL_LATENCY.labels(method=self.labels.get('method', 'unknown')).observe(latency)
            elif self.metric_name == 'fusion':
                FUSION_LATENCY.labels(method=self.labels.get('method', 'unknown')).observe(latency)
            elif self.metric_name == 'rerank':
                RERANK_LATENCY.observe(latency)
            elif self.metric_name == 'llm_generation':
                LLM_GENERATION_LATENCY.observe(latency)


# ==================== API 接口 ====================
@router.get("/metrics")
async def get_prometheus_metrics():
    """获取 Prometheus 格式指标"""
    if not PROMETHEUS_AVAILABLE:
        return {"code": 503, "message": "Prometheus 未安装"}
    
    return Response(
        content=generate_latest(registry),
        media_type=CONTENT_TYPE_LATEST
    )


@router.get("/stats")
async def get_performance_stats():
    """获取性能统计"""
    return {
        "code": 200,
        "data": {
            "summary": performance_tracker.get_summary(),
            "metrics": {
                "rag_request": performance_tracker.get_stats("rag_request"),
                "retrieval": performance_tracker.get_stats("retrieval"),
                "fusion": performance_tracker.get_stats("fusion"),
                "rerank": performance_tracker.get_stats("rerank"),
                "llm_generation": performance_tracker.get_stats("llm_generation")
            }
        }
    }


@router.get("/percentiles")
async def get_percentiles():
    """获取关键百分位数"""
    return {
        "code": 200,
        "data": {
            "latency_p50": performance_tracker.get_percentile("rag_request", 50),
            "latency_p95": performance_tracker.get_percentile("rag_request", 95),
            "latency_p99": performance_tracker.get_percentile("rag_request", 99),
            "retrieval_p95": performance_tracker.get_percentile("retrieval", 95),
            "fusion_p95": performance_tracker.get_percentile("fusion", 95)
        }
    }


@router.post("/record/retrieval")
async def record_retrieval(
    method: str,
    latency: float,
    results_count: int
):
    """记录检索性能"""
    performance_tracker.record_latency(f"retrieval_{method}", latency)
    performance_tracker.record_count(f"retrieval_{method}_count", results_count)
    
    if PROMETHEUS_AVAILABLE:
        RETRIEVAL_LATENCY.labels(method=method).observe(latency)
        RETRIEVAL_RESULTS_COUNT.labels(method=method).observe(results_count)
    
    return {"code": 200, "message": "记录成功"}


@router.post("/record/fusion")
async def record_fusion(
    method: str,
    latency: float,
    input_count: int,
    output_count: int
):
    """记录融合性能"""
    performance_tracker.record_latency("fusion", latency)
    
    if PROMETHEUS_AVAILABLE:
        FUSION_LATENCY.labels(method=method).observe(latency)
        FUSION_INPUT_COUNT.set(input_count)
    
    return {"code": 200, "message": "记录成功"}


@router.post("/record/cache")
async def record_cache(
    hit: bool,
    cache_level: str = "l1"
):
    """记录缓存性能"""
    if PROMETHEUS_AVAILABLE:
        if hit:
            CACHE_HIT_TOTAL.labels(cache_level=cache_level).inc()
        else:
            CACHE_MISS_TOTAL.inc()
    
    return {"code": 200, "message": "记录成功"}


@router.post("/record/context")
async def record_context(
    original_tokens: int,
    compressed_tokens: int
):
    """记录上下文压缩"""
    compression_ratio = compressed_tokens / max(original_tokens, 1)
    
    if PROMETHEUS_AVAILABLE:
        CONTEXT_COMPRESSION_RATIO.set(compression_ratio)
        CONTEXT_TOKENS.observe(compressed_tokens)
    
    return {
        "code": 200,
        "data": {
            "compression_ratio": compression_ratio,
            "saved_tokens": original_tokens - compressed_tokens
        }
    }


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "code": 200,
        "data": {
            "status": "healthy",
            "prometheus_available": PROMETHEUS_AVAILABLE,
            "uptime": performance_tracker.get_summary()["uptime_seconds"]
        }
    }


@router.get("/dashboard")
async def get_dashboard_data():
    """获取仪表盘数据"""
    summary = performance_tracker.get_summary()
    
    return {
        "code": 200,
        "data": {
            "overview": {
                "total_requests": summary["total_requests"],
                "total_errors": summary["total_errors"],
                "error_rate": f"{summary['error_rate'] * 100:.2f}%",
                "requests_per_second": f"{summary['requests_per_second']:.2f}",
                "uptime": f"{summary['uptime_seconds'] / 3600:.2f} 小时"
            },
            "latency": {
                "rag_p95": performance_tracker.get_percentile("rag_request", 95),
                "retrieval_p95": performance_tracker.get_percentile("retrieval", 95),
                "fusion_p95": performance_tracker.get_percentile("fusion", 95)
            },
            "prometheus": {
                "available": PROMETHEUS_AVAILABLE,
                "endpoint": "/api/v1/monitoring/metrics"
            }
        }
    }


# ==================== 中间件 ====================
async def monitoring_middleware(request: Request, call_next):
    """监控中间件"""
    start_time = time.time()
    
    response = await call_next(request)
    
    # 记录请求延迟
    latency = time.time() - start_time
    
    # 记录活跃连接
    if PROMETHEUS_AVAILABLE:
        ACTIVE_CONNECTIONS.inc()
        try:
            ACTIVE_CONNECTIONS.dec()
        except:
            pass
    
    return response
