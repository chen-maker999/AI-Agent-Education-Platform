# Prometheus + Grafana 监控服务使用指南 (P3-002)

## 概述

本监控服务为 RAG 系统提供完整的性能监控和可视化方案，包括：
- **Prometheus**: 指标抓取和存储
- **Grafana**: 可视化仪表板
- **Exporters**: 各组件指标采集（Redis、Elasticsearch、Neo4j、Node）
- **告警规则**: 关键性能指标告警

## 架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Grafana (3000)                          │
│                    可视化仪表板                               │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    Prometheus (9090)                         │
│                  指标抓取和存储                              │
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Node         │ │ Redis        │ │ Elasticsearch│
│ Exporter     │ │ Exporter     │ │ Exporter     │
│ (9100)       │ │ (9121)       │ │ (9114)       │
└──────────────┘ └──────────────┘ └──────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                  RAG Application (8000)                      │
│          /api/v1/monitoring/metrics 端点                     │
└─────────────────────────────────────────────────────────────┘
```

## 快速启动

### 1. 启动监控服务

```bash
cd backend
docker-compose -f docker-compose.monitoring.yml up -d
```

### 2. 验证服务

```bash
# 检查 Prometheus 状态
curl http://localhost:9090/-/healthy

# 检查 Grafana 状态
curl http://localhost:3000/api/health

# 检查各 Exporter
curl http://localhost:9100/metrics      # Node
curl http://localhost:9121/metrics      # Redis
curl http://localhost:9114/metrics      # Elasticsearch
```

### 3. 访问 Grafana

- URL: http://localhost:3000
- 用户名：`admin`
- 密码：`admin123`

导入预置仪表板：
1. 点击 Dashboard → Import
2. 上传 `monitoring/grafana/dashboards/rag_performance.json`
3. 选择 Prometheus 数据源
4. 点击 Import

## 监控指标

### RAG 应用指标

| 指标名称 | 类型 | 描述 |
|---------|------|------|
| `rag_requests_total` | Counter | RAG 请求总数 |
| `rag_request_latency_seconds` | Histogram | RAG 请求延迟 |
| `retrieval_latency_seconds` | Histogram | 检索延迟（按方法） |
| `retrieval_results_count` | Histogram | 检索结果数量 |
| `fusion_latency_seconds` | Histogram | 融合延迟 |
| `rerank_latency_seconds` | Histogram | 重排序延迟 |
| `cache_hits_total` | Counter | 缓存命中数 |
| `cache_misses_total` | Counter | 缓存未命中数 |
| `llm_generation_latency_seconds` | Histogram | LLM 生成延迟 |
| `errors_total` | Counter | 错误总数 |

### 系统资源指标

| 指标名称 | 描述 |
|---------|------|
| `node_cpu_seconds_total` | CPU 使用 |
| `node_memory_*` | 内存使用 |
| `node_filesystem_*` | 磁盘使用 |

### 中间件指标

#### Redis
- `redis_memory_used_bytes`: 内存使用
- `redis_connected_clients`: 连接数
- `redis_ops_per_sec`: 操作速率

#### Elasticsearch
- `elasticsearch_cluster_health_status`: 集群健康
- `elasticsearch_docs_count`: 文档数
- `elasticsearch_jvm_memory_used`: JVM 内存

#### Neo4j
- `neo4j_up`: 服务状态
- `neo4j_jvm_heap_used`: JVM 堆使用
- `neo4j_transactions`: 事务数

## 告警规则

告警规则定义在 `monitoring/prometheus/rag_alerts.yml`：

### 关键告警

| 告警名称 | 阈值 | 级别 |
|---------|------|------|
| RAGServiceDown | 服务宕机 1m | Critical |
| HighRequestLatency | P95 > 1s | Warning |
| CriticalRequestLatency | P95 > 3s | Critical |
| HighErrorRate | 错误率 > 5% | Warning |
| CriticalErrorRate | 错误率 > 10% | Critical |
| LowCacheHitRate | 命中率 < 50% | Warning |
| HighMemoryUsage | 内存 > 85% | Warning |
| HighDiskUsage | 磁盘 > 85% | Warning |

## 在代码中使用监控

### 1. 记录检索性能

```python
from services.knowledge.monitoring.metrics_pusher import metrics_pusher
import time

async def semantic_search(query: str):
    start_time = time.time()
    
    # ... 检索逻辑 ...
    
    duration = time.time() - start_time
    metrics_pusher.observe_histogram(
        "rag_retrieval_duration_seconds",
        duration,
        {"method": "semantic"}
    )
    metrics_pusher.set_gauge(
        "rag_retrieval_results_count",
        len(results),
        {"method": "semantic"}
    )
```

### 2. 记录缓存命中

```python
async def get_embedding(query: str):
    # 尝试缓存
    cached = await cache.get(query)
    if cached:
        metrics_pusher.inc_counter(
            "rag_cache_hits_total",
            1,
            {"cache_level": "redis"}
        )
        return cached
    
    metrics_pusher.inc_counter("rag_cache_misses_total", 1)
    
    # 计算嵌入
    embedding = await compute_embedding(query)
    await cache.set(query, embedding)
    return embedding
```

### 3. 使用上下文管理器

```python
from services.knowledge.monitoring.metrics_pusher import MetricsContext

async def rerank_documents(query, docs):
    with MetricsContext("rag_rerank_duration_seconds"):
        # ... 重排序逻辑 ...
        return ranked_docs
```

### 4. 使用装饰器

```python
from services.knowledge.monitoring.metrics_pusher import track_metrics

@track_metrics("rag_intent_classification_duration_seconds")
async def classify_intent(query: str):
    # ... 意图识别逻辑 ...
    return intent
```

## 更新 Prometheus 配置

如果 RAG 应用运行在 Docker 中，需要更新 `monitoring/prometheus.yml`：

```yaml
scrape_configs:
  - job_name: 'rag-application'
    static_configs:
      - targets: ['host.docker.internal:8000']
    metrics_path: '/api/v1/monitoring/metrics'
```

对于 Linux 系统，可能需要使用 `172.17.0.1:8000` 代替 `host.docker.internal:8000`。

## 停止监控服务

```bash
# 停止所有监控服务
docker-compose -f docker-compose.monitoring.yml down

# 删除数据卷（谨慎使用）
docker-compose -f docker-compose.monitoring.yml down -v
```

## Grafana 仪表板说明

预置的 `rag_performance.json` 仪表板包含以下面板：

### RAG 系统概览
- 错误率
- P95 请求延迟
- 缓存命中率
- 请求吞吐量 (QPS)

### 请求延迟分析
- RAG 请求延迟百分位（P50/P95/P99）
- 各渠道检索延迟 P95（语义/关键词/图谱）

### 检索与融合性能
- 各渠道检索结果数量 P95
- 融合与重排序延迟

### 缓存性能
- 缓存命中/未命中速率
- 缓存大小趋势

### LLM 生成性能
- LLM 生成延迟百分位
- LLM 生成 Token 数

### 系统资源
- CPU 使用率
- 内存使用率
- 磁盘使用率

## 故障排查

### Prometheus 无法抓取 RAG 指标

1. 检查 RAG 应用是否正常启动
2. 验证 `/api/v1/monitoring/metrics` 端点可访问
3. 检查 Prometheus 配置中的目标地址
4. 查看 Prometheus logs: `docker logs rag-prometheus`

### Grafana 无数据显示

1. 确认 Prometheus 数据源配置正确
2. 检查 Prometheus 是否有数据：`http://localhost:9090/graph`
3. 验证仪表板查询语句是否正确

### Exporter 无法连接目标

1. 检查 Docker 网络配置
2. 验证目标服务是否运行
3. 查看 Exporter logs

## 生产环境建议

1. **持久化**: 为 Prometheus 配置持久化存储
2. **高可用**: 部署多套 Prometheus 实例
3. **告警通知**: 集成 Alertmanager 发送邮件/钉钉/企业微信告警
4. **安全**: 配置 Grafana 认证和 HTTPS
5. **保留策略**: 设置合理的指标保留时间（默认 15 天）

## 参考链接

- [Prometheus 官方文档](https://prometheus.io/docs/)
- [Grafana 官方文档](https://grafana.com/docs/)
- [Prometheus 指标类型](https://prometheus.io/docs/concepts/metric_types/)
- [PromQL 入门](https://prometheus.io/docs/prometheus/latest/querying/basics/)
