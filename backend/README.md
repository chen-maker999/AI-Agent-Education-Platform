# AI-Agent-Education-Platform Backend

可嵌入式跨课程AI_Agent通用架构平台后端

## 技术栈

- **Web框架**: FastAPI 0.104
- **数据库**: PostgreSQL 15, Neo4j 5.14, TimescaleDB 2.12
- **消息队列**: RabbitMQ 3.12, Kafka
- **缓存**: Redis 7.0
- **对象存储**: MinIO
- **任务调度**: Celery 5.3
- **AI/ML**: PyTorch 2.1, LangChain, FAISS, sentence-transformers

## 项目结构

```
backend/
├── common/              # 共享模块
│   ├── core/           # 核心配置
│   ├── database/       # 数据库连接
│   ├── middleware/     # 中间件
│   ├── models/         # 通用模型
│   ├── security/       # 安全认证
│   └── utils/          # 工具函数
├── services/           # 微服务
│   ├── base/          # 基础支撑层
│   ├── knowledge/      # 知识管理层
│   ├── data/          # 数据融合层
│   ├── intelligence/  # 智能核心层
│   ├── adapt/         # 平台适配层
│   ├── agent/         # Agent生命周期层
│   └── visual/        # 可视化工具层
├── tests/             # 测试
└── deployment/        # 部署配置
```

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件配置数据库、Redis等
```

### 运行服务

```bash
# 运行所有服务
docker-compose up -d

# 或单独运行某个服务
uvicorn services.base.auth.main:app --reload
```

## API文档

服务启动后访问:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 开发

```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 运行测试
pytest

# 代码格式检查
ruff check .
```
