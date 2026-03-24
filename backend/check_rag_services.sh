#!/bin/bash
# RAG 环境服务健康检查脚本

echo "=========================================="
echo "  RAG 环境服务健康检查"
echo "=========================================="

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_service() {
    local name=$1
    local cmd=$2
    local expected=$3
    
    echo -n "检查 $name ... "
    if eval "$cmd" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 正常${NC}"
        return 0
    else
        echo -e "${RED}✗ 失败${NC}"
        return 1
    fi
}

# PostgreSQL
check_service "PostgreSQL" "docker exec edu-postgres pg_isready -U postgres"
POSTGRES_STATUS=$?

# Redis (本地服务)
check_service "Redis" "redis-cli ping"
REDIS_STATUS=$?

# Neo4j
check_service "Neo4j" "curl -s http://localhost:7474/db/data/"
NEO4J_STATUS=$?

# Elasticsearch
check_service "Elasticsearch" "curl -s http://localhost:9200/_cluster/health | grep -q '\"status\":\"green\"'"
ES_STATUS=$?

# MinIO
check_service "MinIO" "curl -s -o /dev/null -w '%{http_code}' http://localhost:9000/minio/health/live | grep -q '200'"
MINIO_STATUS=$?

echo ""
echo "=========================================="
echo "  服务端口信息"
echo "=========================================="
echo "PostgreSQL:    localhost:5432"
echo "Redis:         localhost:6379"
echo "Neo4j:         localhost:7474 (HTTP), localhost:7687 (Bolt)"
echo "Elasticsearch: localhost:9200"
echo "MinIO:         localhost:9000 (API), localhost:9001 (Console)"
echo ""

# Docker 容器状态
echo "=========================================="
echo "  Docker 容器状态"
echo "=========================================="
docker ps --filter "name=edu-" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "=========================================="
echo "  总结"
echo "=========================================="

TOTAL=5
PASSED=0

[ $POSTGRES_STATUS -eq 0 ] && ((PASSED++))
[ $REDIS_STATUS -eq 0 ] && ((PASSED++))
[ $NEO4J_STATUS -eq 0 ] && ((PASSED++))
[ $ES_STATUS -eq 0 ] && ((PASSED++))
[ $MINIO_STATUS -eq 0 ] && ((PASSED++))

echo "通过：$PASSED/$TOTAL"

if [ $PASSED -eq $TOTAL ]; then
    echo -e "${GREEN}所有服务正常运行!${NC}"
    exit 0
else
    echo -e "${RED}部分服务异常，请检查日志${NC}"
    exit 1
fi
