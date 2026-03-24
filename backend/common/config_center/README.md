# 配置中心使用指南 - P3-001

## 概述

配置中心提供统一的配置管理，支持热更新和多种后端存储，解决配置分散、变更需重启的问题。

### 核心功能

- ✅ **统一管理**: 所有配置集中在一个地方管理
- ✅ **热更新**: 修改配置无需重启服务
- ✅ **多种后端**: 支持本地文件、etcd、Consul
- ✅ **变更通知**: 配置变更自动通知相关模块
- ✅ **版本管理**: 记录配置版本和变更历史
- ✅ **类型安全**: 支持类型化的配置读取

---

## 快速开始

### 1. 初始化配置中心

```python
from common.config_center import setup_config_center_from_env, config_center

# 在应用启动时初始化
await setup_config_center_from_env()
```

### 2. 读取配置

```python
from common.config_center import get_config, get_config_typed

# 简单读取
rrf_k = get_config("rag.fusion.rrf_k", default=60)

# 类型化读取
max_tokens = get_config_typed("rag.context.max_tokens", type_hint=int)
enabled = get_config_typed("rag.cache.enabled", type_hint=bool)

# 获取完整配置
all_configs = config_center.get_all()
```

### 3. 更新配置（热更新）

```python
from common.config_center import set_config

# 更新配置
await set_config("rag.fusion.semantic_weight", 0.5, updated_by="admin")

# 配置立即生效，无需重启
```

### 4. 注册配置变更回调

```python
from common.config_center import register_config_callback

async def on_weight_change(key: str, new_value):
    print(f"权重更新：{key} = {new_value}")
    # 重新加载相关模块的配置

register_config_callback("rag.fusion.semantic_weight", on_weight_change)
```

---

## 配置项列表

### RAG 检索配置

| 配置键 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `rag.fusion.rrf_k` | int | 60 | RRF 融合参数 k |
| `rag.fusion.semantic_weight` | float | 0.4 | 语义检索权重 |
| `rag.fusion.keyword_weight` | float | 0.3 | 关键词检索权重 |
| `rag.fusion.graph_weight` | float | 0.3 | 图谱检索权重 |
| `rag.retrieval.top_k` | int | 10 | 检索结果数量 |
| `rag.retrieval.timeout_seconds` | int | 5 | 检索超时时间 |
| `rag.retrieval.use_rerank` | bool | true | 是否启用重排序 |
| `rag.retrieval.use_rewrite` | bool | true | 是否启用查询改写 |
| `rag.context.max_tokens` | int | 3000 | 上下文最大 token 数 |
| `rag.context.use_diversity` | bool | true | 是否启用多样性选择 |
| `rag.context.mmr_lambda` | float | 0.5 | MMR 多样性参数 |
| `rag.cache.enabled` | bool | true | 是否启用缓存 |
| `rag.cache.ttl_seconds` | int | 86400 | 缓存 TTL（秒） |

### Elasticsearch 配置

| 配置键 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `elasticsearch.host` | str | localhost | ES 主机地址 |
| `elasticsearch.port` | int | 9200 | ES 端口 |
| `elasticsearch.index` | str | edu_bm25 | ES 索引名 |

### Kimi API 配置

| 配置键 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `kimi.timeout` | int | 30 | API 超时时间（秒） |
| `kimi.max_retries` | int | 3 | 最大重试次数 |

### 限流配置

| 配置键 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `rate_limit.enabled` | bool | true | 是否启用限流 |
| `rate_limit.default_requests` | int | 60 | 默认请求数限制 |
| `rate_limit.default_window` | int | 60 | 默认时间窗口（秒） |
| `rate_limit.bucket_capacity` | int | 100 | 令牌桶容量 |
| `rate_limit.bucket_refill_rate` | float | 10 | 令牌补充速率 |

### 监控配置

| 配置键 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `monitoring.enabled` | bool | true | 是否启用监控 |
| `monitoring.prometheus_port` | int | 9090 | Prometheus 端口 |
| `logging.level` | str | INFO | 日志级别 |

---

## API 接口

配置中心提供完整的 REST API，支持配置的 CRUD 操作。

### 获取配置状态

```bash
GET /api/v1/config/
```

### 获取单个配置

```bash
GET /api/v1/config/get?key=rag.fusion.rrf_k&include_metadata=true
```

### 设置配置（热更新）

```bash
POST /api/v1/config/set
Content-Type: application/json

{
  "key": "rag.fusion.semantic_weight",
  "value": 0.5,
  "updated_by": "admin"
}
```

### 获取所有配置

```bash
GET /api/v1/config/list?include_metadata=true
```

### 刷新配置

```bash
POST /api/v1/config/refresh
```

### 导出配置

```bash
GET /api/v1/config/export?format=json
GET /api/v1/config/export?format=env
```

### 比较配置差异

```bash
GET /api/v1/config/diff
```

---

## 后端存储

### 本地文件后端（开发环境）

```python
from common.config_center import config_center

await config_center.initialize(
    backend_type="local",
    config_path="data/config/config.json",
    auto_refresh=True,
    refresh_interval=30  # 每 30 秒自动刷新
)
```

### etcd 后端（生产环境）

```python
await config_center.initialize(
    backend_type="etcd",
    etcd_host="localhost",
    etcd_port=2379,
    auto_refresh=False
)
```

### 环境变量配置

```bash
# 配置中心
CONFIG_BACKEND=local          # 后端类型：local | etcd | consul
CONFIG_PATH=data/config/config.json  # 本地配置文件路径
ETCD_HOST=localhost           # etcd 主机
ETCD_PORT=2379                # etcd 端口
CONFIG_AUTO_REFRESH=true      # 是否自动刷新
CONFIG_REFRESH_INTERVAL=30    # 刷新间隔（秒）
```

---

## 使用场景

### 场景 1：动态调整 RAG 融合权重

```python
# 发现语义检索效果不好，临时调高关键词权重
await set_config("rag.fusion.keyword_weight", 0.5, updated_by="ops")
await set_config("rag.fusion.semantic_weight", 0.2, updated_by="ops")

# 配置立即生效，无需重启服务
```

### 场景 2：A/B 测试不同参数

```python
# A 组：RRF k=60
await set_config("rag.fusion.rrf_k", 60, updated_by="ab_test_a")

# 运行一段时间后，切换到 B 组：RRF k=40
await set_config("rag.fusion.rrf_k", 40, updated_by="ab_test_b")

# 比较两组的检索效果
```

### 场景 3：紧急情况降级

```python
# Kimi API 不稳定，临时关闭查询改写
await set_config("rag.retrieval.use_rewrite", False, updated_by="oncall")

# 问题修复后恢复
await set_config("rag.retrieval.use_rewrite", True, updated_by="oncall")
```

### 场景 4：性能调优

```python
# 调大缓存 TTL，减少嵌入计算
await set_config("rag.cache.ttl_seconds", 172800, updated_by="perf_tuning")

# 调大检索超时，提高召回率
await set_config("rag.retrieval.timeout_seconds", 10, updated_by="perf_tuning")
```

---

## 最佳实践

### 1. 配置命名规范

- 使用点分隔的层级命名：`service.module.setting`
- 使用小写字母和下划线：`semantic_weight`
- 布尔值使用 `enabled`、`use_` 前缀

### 2. 配置变更审计

所有配置变更都会记录：
- 变更时间
- 变更者
- 旧值和新值
- 版本号

### 3. 配置验证

在设置配置前进行验证：

```bash
POST /api/v1/config/validate
{
  "key": "rag.fusion.semantic_weight",
  "value": 0.5
}
```

### 4. 配置备份

定期导出配置备份：

```bash
GET /api/v1/config/export?format=json
```

### 5. 配置回滚

保留历史版本，支持快速回滚：

```python
# 记录当前配置
old_weight = get_config("rag.fusion.semantic_weight")

# 更新配置
await set_config("rag.fusion.semantic_weight", 0.6)

# 如果效果不好，回滚
await set_config("rag.fusion.semantic_weight", old_weight)
```

---

## 故障排查

### 问题 1：配置不生效

**检查清单**:
1. 配置中心是否已初始化
2. 配置键是否正确
3. 相关模块是否注册了回调
4. 配置文件是否有写权限

### 问题 2：etcd 连接失败

**解决方案**:
1. 检查 etcd 服务是否运行
2. 检查网络连接
3. 检查 etcd 地址和端口配置
4. 降级到本地文件后端

### 问题 3：配置回调未触发

**检查清单**:
1. 回调函数是否正确注册
2. 回调函数是否抛出异常
3. 配置值是否真的改变

---

## 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                    应用层 (Application)                   │
├─────────────────────────────────────────────────────────┤
│  API 路由  │  配置变更回调  │  热更新示例                 │
├─────────────────────────────────────────────────────────┤
│                   配置中心 (ConfigCenter)                │
│  - 配置读取/写入  - 变更通知  - 版本管理  - 自动刷新      │
├─────────────────────────────────────────────────────────┤
│                   后端接口 (Backend)                     │
│  ┌──────────────────┐  ┌──────────────────┐            │
│  │  LocalFileBackend │  │    EtcdBackend    │            │
│  │  - JSON 文件存储   │  │  - 分布式 KV 存储   │            │
│  │  - 自动刷新       │  │  - Watch 监听     │            │
│  └──────────────────┘  └──────────────────┘            │
└─────────────────────────────────────────────────────────┘
```

---

## 相关文件

- `backend/common/config_center/main.py` - 配置中心核心实现
- `backend/common/config_center/routes.py` - API 路由
- `backend/common/config_center/hot_reload_example.py` - 热更新示例
- `backend/data/config/config.json` - 默认配置文件
- `backend/test_config_center.py` - 测试脚本

---

## 下一步

- [ ] P3-002: Prometheus 监控集成
- [ ] P3-004: Prompt 版本管理
- [ ] P4-004: 基于配置中心的在线学习
