# AI-Agent 教育平台

> **可嵌入式跨课程 AI_Agent 通用架构平台** —— 基于大模型（LLM）的智能教育辅助系统，提供作业智能批改、知识库问答、个性化学习预警、工作表生成等核心能力。

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![Vue.js](https://img.shields.io/badge/Vue-3.x-42b883?style=flat-square&logo=vue.js)](https://vuejs.org)
[![Next.js](https://img.shields.io/badge/Next.js-15.x-000000?style=flat-square&logo=next.js)](https://nextjs.org)
[![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=flat-square&logo=python)](https://python.org)

---

## 平台架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        前端层                                    │
│  ┌─────────────────┐  ┌──────────────┐  ┌─────────────────────┐  │
│  │  Next.js (AI页) │  │ Vue 3 (管理)  │  │  知识图谱可视化      │  │
│  └─────────────────┘  └──────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │ HTTP / WebSocket
┌─────────────────────────────────────────────────────────────────┐
│                      API 网关层 (FastAPI)                        │
│  Auth │ Roles │ Registry │ Config │ Flow │ Scheduler │ Cache      │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                      核心服务层 (微服务模块化)                     │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Intelligence │  │   Knowledge   │  │       Agent          │  │
│  │  ────────────│  │  ────────────│  │  ────────────────────│  │
│  │  · 智能对话   │  │  · 向量检索   │  │  · 模板管理          │  │
│  │  · 作业批改   │  │  · 混合搜索   │  │  · 部署/销毁         │  │
│  │  · 作业生成   │  │  · RAG 检索   │  │  · 工具注册          │  │
│  │  · 习题生成   │  │  · ES 索引   │  │  · CRUD + 对话       │  │
│  │  · 预警系统   │  │  · 知识图谱   │  │                      │  │
│  │  · 标注/评估  │  │  · 知识点管理 │  │                      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │    Data       │  │    Base      │  │      Adapt           │  │
│  │  ────────────│  │  ────────────│  │  ────────────────────│  │
│  │  · 作业管理   │  │  · JWT 认证  │  │  · 适配网关          │  │
│  │  · 学生画像   │  │  · 权限管理  │  │  · 数据同步          │  │
│  │  · 反馈收集   │  · Redis 缓存 │  │                      │  │
│  │  · 时序数据   │  │              │  │                      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                      数据与存储层                                 │
│                                                                  │
│  PostgreSQL │ Redis │ Neo4j │ Elasticsearch │ MinIO │ FAISS     │
│  TimescaleDB │ Kafka │ RabbitMQ │ Consul                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 核心技术栈

| 层级 | 技术选型 |
|------|---------|
| **后端框架** | FastAPI 0.109 + Uvicorn、Python 3.13 |
| **前端（管理）** | Vue 3 + Vite + TypeScript |
| **前端（AI 页）** | Next.js 15 + React 19 |
| **AI 大模型** | Kimi (Moonshot) —— 多模态（文本/视觉）LLM |
| **向量检索** | FAISS + Sentence-Transformers (all-MiniLM-L6-v2) |
| **全文检索** | Elasticsearch (混合搜索) |
| **关系图谱** | Neo4j (知识图谱存储与查询) |
| **关系数据库** | PostgreSQL + TimescaleDB（时序扩展） |
| **缓存** | Redis |
| **文件存储** | MinIO (S3 兼容对象存储) |
| **消息队列** | Kafka + RabbitMQ |
| **任务队列** | Celery |
| **服务注册** | Consul |
| **作业批改** | ReportLab（PDF 生成）、python-docx（批注注入） |

---

## 核心功能模块

### 1. AI 智能对话（Chat + RAG）
- 基于 **Kimi 多模态大模型**，支持文本和图片输入
- 完整 **RAG（检索增强生成）** 流程：分块 → 向量化 → 混合搜索 → 重排序 → 生成
- 支持多种检索策略：向量检索（FAISS）、BM25、ES 全文检索
- 聊天历史持久化（PostgreSQL）、消息来源追踪、用户评分反馈
- 知识点关联，自动关联用户问题与知识库中的知识点

### 2. 作业智能批改（Homework Review）
- 接收学生提交的 `.docx` / `.doc` 作业文件
- AI 自动提取代码内容、识别错误（规则引擎 + 大模型辅助）
- 将批注（评语、扣分点）注入 Word 文档，生成带批注的新文件
- 分数计算、批改历史记录存储
- 支持教师上传参考答案模板进行对比评分

### 3. 作业/工作表生成（Homework Gen）
- 基于知识库内容和大模型，**自动生成配套练习题**
- 支持多种题型：选择题、填空题、判断题、简答题
- 题目难度可调（Difficult / Medium / Easy）
- 生成 **CJK（中文）PDF**，支持宋体/黑体字体
- 按课程（course）隔离，支持工作表状态追踪

### 4. 学习风险预警（Warning System）
- 三层预警机制：**高危（high）/ 中危（medium）/ 低危（low）**
- 基于时序数据（TimescaleDB）监控学生学习行为
- 预警类型：注意力下降、成绩波动、参与度降低
- 提供风险评分、预警描述、改进建议
- 预警规则可配置（阈值、开关）

### 5. 学生画像（Portrait）
- 自动构建学生学习画像
- 学习风格识别、知识掌握度分析
- 优势/劣势领域识别
- 研究方向推荐

### 6. Agent 可编程平台（Agent Studio）
- **模板管理**：创建/编辑 Agent 对话模板
- **工具注册**：灵活扩展 Agent 可调用工具集（Tools Registry）
- **部署/销毁**：动态创建和销毁 Agent 实例
- **会话管理**：完整 CRUD，支持流式对话（Server-Sent Events）
- **多模态支持**：上传图片、URL 内容抓取，Agent 实时理解

### 7. 知识图谱可视化
- 基于 Neo4j 存储课程知识点关系
- 可视化展示知识点的层级结构和依赖关系

---

## 项目目录结构

```
AI-Agent-Education-Platform/
├── backend/                          # FastAPI 后端
│   ├── main.py                        # 应用入口，路由注册
│   ├── requirements.txt                # Python 依赖
│   ├── common/                        # 公共模块
│   │   ├── core/config.py             # 配置管理（所有中间件配置）
│   │   ├── database/                  # 数据库连接
│   │   │   ├── postgresql.py          # AsyncPG 连接池
│   │   │   ├── redis.py               # Redis 连接
│   │   │   └── neo4j.py               # Neo4j 连接
│   │   ├── integration/
│   │   │   └── kimi.py               # Kimi API 客户端（多模态）
│   │   ├── models/
│   │   │   └── response.py           # 统一响应模型
│   │   └── security/
│   │       └── jwt.py                 # JWT 认证
│   └── services/                      # 业务微服务
│       ├── intelligence/              # AI 智能服务
│       │   ├── chat/                  # 智能对话 + RAG
│       │   ├── homework_gen/          # 作业/习题 PDF 生成
│       │   ├── parse/                 # 文档解析
│       │   ├── evaluate/              # 评估服务
│       │   ├── warning/               # 学习风险预警
│       │   ├── annotation/            # 文档标注
│       │   ├── exercise/              # 习题服务
│       │   └── worksheet/             # 工作表管理
│       ├── knowledge/                 # 知识管理
│       │   ├── rag/                   # RAG 核心
│       │   ├── vector/               # 向量存储（FAISS）
│       │   ├── embedding/            # Embedding 生成
│       │   ├── es_indexer/           # ES 索引管理
│       │   ├── search/               # 混合搜索
│       │   ├── rerank/               # Cross-Encoder 重排
│       │   ├── chunk/                 # 文档分块
│       │   ├── trimmer/              # 文本裁剪
│       │   ├── fusion/               # 多路召回融合
│       │   ├── router/               # 查询路由
│       │   ├── points/               # 知识点管理
│       │   ├── graph/                # Neo4j 知识图谱
│       │   ├── query_rewrite/        # 查询改写
│       │   ├── faiss_indexer/        # FAISS 索引构建
│       │   ├── bm25_main/            # BM25 检索
│       │   └── library/              # 知识库管理
│       ├── agent/                      # Agent 平台
│       │   ├── template/             # Agent 模板
│       │   ├── deploy/               # Agent 部署
│       │   ├── destroy/              # Agent 销毁
│       │   ├── tools/                # 工具注册表
│       │   ├── crud/                 # Agent 会话 CRUD
│       │   └── data/sessions/        # 会话数据存储
│       ├── data/                      # 数据管理
│       │   ├── homework/             # 作业管理
│       │   ├── homework_review/      # 作业批改（docx 批注注入）
│       │   ├── portrait/            # 学生画像
│       │   ├── feedback/            # 反馈收集
│       │   ├── collect/             # 数据采集
│       │   └── timeseries/          # 时序数据
│       ├── base/                      # 基础能力
│       │   ├── auth/                 # JWT 认证
│       │   ├── roles/               # RBAC 权限
│       │   ├── registry/            # 服务注册
│       │   ├── config/              # 配置中心
│       │   ├── flow/                # 工作流
│       │   ├── scheduler/            # 定时任务
│       │   └── cache/               # Redis 缓存
│       ├── adapt/                    # 适配层
│       │   ├── gateway/              # 适配网关
│       │   └── sync/                 # 数据同步
│       └── visual/                   # 可视化
│           └── display/              # 图表/数据展示
│
├── class_system/frontend/src/         # Vue 3 管理后台前端
│   ├── views/                        # 页面视图
│   │   ├── Chat.vue                 # AI 对话页
│   │   ├── Homework.vue             # 作业管理
│   │   ├── KnowledgeGraph.vue       # 知识图谱
│   │   ├── Warning.vue              # 学习预警
│   │   ├── Portrait.vue             # 学生画像
│   │   ├── Studio.vue               # Agent 工作台
│   │   ├── Evaluation.vue            # 评估页
│   │   ├── AgentConfig.vue          # Agent 配置
│   │   ├── Dashboard.vue            # 数据仪表盘
│   │   ├── Login.vue / Register.vue  # 认证页
│   │   └── Settings.vue             # 设置页
│   └── components/                   # 通用组件
│
├── AI/                               # Next.js AI 功能页（保留目录）
└── README.md                         # 本文件
```

---

## API 接口概览

所有接口统一前缀 `/api/v1`，返回格式为 `ResponseModel`。

| 路由前缀 | 功能 | 核心接口 |
|---------|------|---------|
| `/auth` | JWT 认证 | 登录、注册、Token 刷新 |
| `/roles` | 权限管理 | RBAC 角色/权限查询 |
| `/homework` | 作业管理 | 上传、查询、下载 |
| `/homework-review` | 作业批改 | 提交批改请求、查询批改结果 |
| `/homework-gen` | 作业生成 | 基于知识库生成 PDF 作业 |
| `/chat` | AI 对话 | 流式对话、RAG 检索、历史记录 |
| `/knowledge` | 知识库 | 上传文档、分块、向量化 |
| `/knowledge/vector` | 向量索引 | FAISS 构建与检索 |
| `/knowledge/search` | 混合搜索 | ES + BM25 + FAISS 多路召回 |
| `/knowledge/rerank` | 重排序 | Cross-Encoder 重排 |
| `/knowledge/graph` | 知识图谱 | Neo4j 图谱 CRUD |
| `/warning` | 学习预警 | 预警生成、查询、处理 |
| `/portrait` | 学生画像 | 画像生成与查询 |
| `/worksheet` | 工作表 | 习题集管理 |
| `/agent` | Agent 平台 | 创建、对话、工具调用 |
| `/feedback` | 反馈 | 对话/作业反馈收集 |

---

## 快速启动

### 环境要求

- Python 3.13+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- MinIO（可选，文件存储）
- Neo4j（可选，知识图谱）
- Elasticsearch 8+（可选，混合搜索）
- Kimi API Key（`KIMI_API_KEY`）

### 后端启动

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env，填写 KIMI_API_KEY 等配置

# 启动服务（数据库表会自动创建）
python main.py
# 或
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

API 文档访问：`http://localhost:8000/docs`

### 前端启动（Vue 管理后台）

```bash
cd class_system/frontend

npm install
npm run dev
```

### Next.js AI 页

```bash
npm install
npm run dev
```

---

## 环境变量说明

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `KIMI_API_KEY` | Moonshot Kimi API 密钥 | - |
| `POSTGRES_HOST` | PostgreSQL 主机 | localhost |
| `POSTGRES_DB` | 数据库名 | edu_platform |
| `REDIS_HOST` | Redis 主机 | localhost |
| `MINIO_ENDPOINT` | MinIO 地址 | localhost:9000 |
| `NEO4J_HOST` | Neo4j 主机 | localhost |
| `ELASTICSEARCH_HOST` | ES 主机 | localhost |
| `SECRET_KEY` | JWT 签名密钥 | (需修改) |

---

## 数据库表

启动时自动创建以下核心表：

`users` · `homework` · `homework_reviews` · `portraits` · `feedbacks` · `timeseries_data` · `knowledge_points` · `chat_sessions` · `chat_messages` · `chat_feedback` · `warnings` · `warning_rules` · `rag_documents` · `rag_sessions` · `vector_documents` · `worksheets`

---

## License

MIT
