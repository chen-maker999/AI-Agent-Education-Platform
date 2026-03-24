#!/bin/bash
# AI-Agent-Education-Platform 服务一键启动脚本
# 使用方法：./start_services.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# 检查 Docker 是否运行
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    if ! docker ps &> /dev/null; then
        log_error "Docker 未运行，请启动 Docker 服务"
        exit 1
    fi
    
    log_success "Docker 运行正常"
}

# 创建 .env 文件
create_env_file() {
    if [ ! -f ".env" ]; then
        log_info "创建 .env 配置文件..."
        cat > .env << 'EOF'
# ===========================================
# AI-Agent-Education-Platform 环境配置
# ===========================================

# App 设置
APP_NAME=AI-Agent-Education-Platform
APP_VERSION=1.0.0
DEBUG=true
API_PREFIX=/api/v1

# 服务器
HOST=0.0.0.0
PORT=8000

# ===========================================
# 数据库配置
# ===========================================

# PostgreSQL (主数据库)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=edu_platform

# TimescaleDB (时序数据库)
TIMESCALEDB_HOST=localhost
TIMESCALEDB_PORT=5433
TIMESCALEDB_USER=postgres
TIMESCALEDB_PASSWORD=postgres
TIMESCALEDB_DB=timeseries

# Redis (缓存)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Neo4j (知识图谱)
NEO4J_HOST=localhost
NEO4J_PORT=7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4j
NEO4J_DATABASE=neo4j

# Elasticsearch (关键词检索)
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_INDEX=edu_knowledge

# MinIO (对象存储)
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_SECURE=false
MINIO_BUCKET_HOMEWORK=edu-homework
MINIO_BUCKET_COURSEWARE=edu-courseware
MINIO_BUCKET_LAKE=edu-lake

# RabbitMQ (消息队列)
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
RABBITMQ_VHOST=/

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# JWT 配置
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# Kimi API (Moonshot)
# KIMI_API_KEY=your-kimi-api-key-here
KIMI_API_ENDPOINT=https://api.moonshot.cn/v1
KIMI_MODEL=moonshot-v1-128k
KIMI_TIMEOUT=30

# FAISS 向量索引
FAISS_INDEX_TYPE=IVF4096,PQ16
FAISS_DIMENSION=384
FAISS_NLIST=4096
FAISS_NPROBE=32

# Embedding 模型
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DEVICE=cpu
EMBEDDING_BATCH_SIZE=64
EMBEDDING_MAX_LENGTH=512
EMBEDDING_DIMENSION=384

# Cross-Encoder (重排序)
CROSS_ENCODER_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2

# CORS
CORS_ORIGINS=["*"]
EOF
        log_success ".env 文件创建成功"
    else
        log_info ".env 文件已存在，跳过创建"
    fi
}

# 启动 Docker 容器
start_docker_services() {
    log_info "启动 Docker 容器服务..."
    
    # 使用 docker-compose.rag.yml 启动核心 RAG 服务
    if [ -f "docker-compose.rag.yml" ]; then
        log_info "使用 docker-compose.rag.yml 启动 RAG 核心服务..."
        docker compose -f docker-compose.rag.yml up -d
        
        # 等待服务启动
        log_info "等待服务启动 (30 秒)..."
        sleep 30
    else
        log_error "docker-compose.rag.yml 不存在"
        exit 1
    fi
    
    log_success "Docker 容器启动完成"
}

# 检查服务健康状态
check_services() {
    log_info "检查服务健康状态..."
    
    local passed=0
    local total=5
    
    # PostgreSQL
    echo -n "  检查 PostgreSQL ... "
    if docker exec edu-postgres pg_isready -U postgres &> /dev/null; then
        echo -e "${GREEN}✓ 正常${NC}"
        ((passed++))
    else
        echo -e "${RED}✗ 失败${NC}"
    fi
    
    # Redis
    echo -n "  检查 Redis ... "
    if docker exec edu-redis redis-cli ping &> /dev/null; then
        echo -e "${GREEN}✓ 正常${NC}"
        ((passed++))
    else
        echo -e "${RED}✗ 失败${NC}"
    fi
    
    # Neo4j
    echo -n "  检查 Neo4j ... "
    if curl -s http://localhost:7474/db/data/ &> /dev/null; then
        echo -e "${GREEN}✓ 正常${NC}"
        ((passed++))
    else
        echo -e "${RED}✗ 失败${NC}"
    fi
    
    # Elasticsearch
    echo -n "  检查 Elasticsearch ... "
    if curl -s http://localhost:9200/_cluster/health &> /dev/null; then
        echo -e "${GREEN}✓ 正常${NC}"
        ((passed++))
    else
        echo -e "${RED}✗ 失败${NC}"
    fi
    
    # MinIO
    echo -n "  检查 MinIO ... "
    if curl -s -o /dev/null -w '%{http_code}' http://localhost:9000/minio/health/live | grep -q '200'; then
        echo -e "${GREEN}✓ 正常${NC}"
        ((passed++))
    else
        echo -e "${RED}✗ 失败${NC}"
    fi
    
    echo ""
    echo "  通过：$passed/$total"
    
    if [ $passed -eq $total ]; then
        log_success "所有服务运行正常"
        return 0
    else
        log_warn "部分服务异常，请检查日志"
        return 1
    fi
}

# 初始化数据库表
init_database() {
    log_info "初始化数据库表..."
    
    # 激活虚拟环境
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    else
        log_warn ".venv 目录不存在，跳过数据库初始化"
        return 0
    fi
    
    # 等待 PostgreSQL 完全启动
    log_info "等待 PostgreSQL 完全启动..."
    sleep 5
    
    # 运行初始化脚本
    if [ -f "init_neo4j_schema.py" ]; then
        log_info "初始化 Neo4j 知识图谱..."
        python init_neo4j_schema.py || log_warn "Neo4j 初始化失败"
    fi
    
    if [ -f "init_minio_buckets.py" ]; then
        log_info "初始化 MinIO 存储桶..."
        python init_minio_buckets.py || log_warn "MinIO 初始化失败"
    fi
    
    log_success "数据库初始化完成"
}

# 显示服务信息
show_service_info() {
    echo ""
    echo -e "${GREEN}==========================================${NC}"
    echo -e "${GREEN}  服务启动完成!${NC}"
    echo -e "${GREEN}==========================================${NC}"
    echo ""
    echo "服务访问信息:"
    echo "  PostgreSQL:    localhost:5432 (postgres/postgres)"
    echo "  Redis:         localhost:6379"
    echo "  Neo4j:         http://localhost:7474 (neo4j/neo4j)"
    echo "  Elasticsearch: http://localhost:9200"
    echo "  MinIO:         http://localhost:9001 (minioadmin/minioadmin)"
    echo ""
    echo "后端 API:"
    echo "  Swagger UI:    http://localhost:8000/docs"
    echo "  ReDoc:         http://localhost:8000/redoc"
    echo ""
    echo "启动后端服务:"
    echo "  source .venv/bin/activate"
    echo "  uvicorn main:app --reload --host 0.0.0.0 --port 8000"
    echo ""
}

# 主函数
main() {
    echo -e "${BLUE}==========================================${NC}"
    echo -e "${BLUE}  AI-Agent-Education-Platform 服务启动${NC}"
    echo -e "${BLUE}==========================================${NC}"
    echo ""
    
    check_docker
    create_env_file
    start_docker_services
    check_services
    init_database
    show_service_info
}

# 运行主函数
main "$@"
