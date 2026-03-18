"""Main FastAPI application - aggregates all services."""

import asyncio
# Windows 上使用 SelectorEventLoop 避免 Proactor 问题
import sys
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from common.core.config import settings
from common.models.response import ResponseModel
from services.base.auth.main import router as auth_router
from services.base.roles.main import router as roles_router
from services.base.registry.main import router as registry_router
from services.base.config.main import router as config_router
from services.base.flow.main import router as flow_router
from services.base.scheduler.main import router as scheduler_router
from services.base.cache.main import router as cache_router
from services.data.collect.main import router as collect_router
from services.data.homework.main import router as homework_router
from services.data.portrait.main import router as portrait_router
from services.data.timeseries.main import router as timeseries_router
from services.data.feedback.main import router as feedback_router
from services.knowledge.points.main import router as knowledge_router
from services.knowledge.points.main import router as knowledge_router
from services.knowledge.graph.main import router as graph_router
from services.knowledge.vector.main import router as vector_router
from services.knowledge.chunk.main import router as chunk_router
from services.knowledge.embedding.main import router as embedding_router
from services.knowledge.faiss_indexer.main import router as faiss_router
from services.knowledge.es_indexer.main import router as es_router
from services.knowledge.query_rewrite.main import router as query_rewrite_router
from services.knowledge.router.main import router as router_router
from services.knowledge.search.main import router as search_router
from services.knowledge.fusion.main import router as fusion_router
from services.knowledge.rerank.main import router as rerank_router
from services.knowledge.trimmer.main import router as trimmer_router
from services.knowledge.rag.main import router as rag_router
from services.knowledge.library.main import router as library_router
from services.intelligence.chat.main import router as chat_router
from services.intelligence.annotation.main import router as annotation_router
from services.intelligence.evaluate.main import router as evaluate_router
from services.intelligence.parse.main import router as parse_router
from services.intelligence.exercise.main import router as exercise_router
from services.intelligence.warning.main import router as warning_router
from services.adapt.gateway.main import router as gateway_router
from services.adapt.sync.main import router as sync_router
from services.agent.template.main import router as agent_template_router
from services.agent.deploy.main import router as agent_deploy_router
from services.agent.destroy.main import router as agent_destroy_router
from services.visual.display.main import router as visual_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="可嵌入式跨课程AI_Agent通用架构平台后端API",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Create database tables on startup."""
    from sqlalchemy import text
    from common.database.postgresql import async_engine
    
    # 先删除可能存在的旧表
    drop_tables_sql = [
        "DROP TABLE IF EXISTS chat_feedback",
        "DROP TABLE IF EXISTS chat_messages",
        "DROP TABLE IF EXISTS chat_sessions",
        "DROP TABLE IF EXISTS knowledge_points",
        "DROP TABLE IF EXISTS feedbacks",
        "DROP TABLE IF EXISTS timeseries_data",
        "DROP TABLE IF EXISTS portraits",
        "DROP TABLE IF EXISTS homework",
        "DROP TABLE IF EXISTS warning_rules",
        "DROP TABLE IF EXISTS warnings",
        "DROP TABLE IF EXISTS users",
        "DROP TABLE IF EXISTS rag_documents",
        "DROP TABLE IF EXISTS rag_sessions",
        "DROP TABLE IF EXISTS vector_documents",
    ]
    
    async with async_engine.begin() as conn:
        for sql in drop_tables_sql:
            try:
                await conn.execute(text(sql))
            except Exception as e:
                print(f"Drop warning: {e}")
    
    print("Old tables dropped!")
    
    # 创建所有需要的数据库表
    tables_sql = [
        # 用户表
        """CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            hashed_password VARCHAR(255) NOT NULL,
            role VARCHAR(20) DEFAULT 'student',
            status VARCHAR(20) DEFAULT 'active',
            roles VARCHAR(500) DEFAULT '[]',
            permissions VARCHAR(1000) DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        # 作业表
        """CREATE TABLE IF NOT EXISTS homework (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            homework_id VARCHAR(255) UNIQUE NOT NULL,
            student_id VARCHAR(255) NOT NULL,
            filename VARCHAR(500) NOT NULL,
            file_url TEXT NOT NULL,
            file_hash VARCHAR(64) NOT NULL,
            file_size INTEGER NOT NULL,
            mime_type VARCHAR(100) NOT NULL,
            status VARCHAR(50) DEFAULT 'pending',
            course VARCHAR(100),
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        # 画像表
        """CREATE TABLE IF NOT EXISTS portraits (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            student_id VARCHAR(255) UNIQUE NOT NULL,
            name VARCHAR(255),
            avatar_url TEXT,
            learning_style VARCHAR(50),
            intro_zh TEXT,
            intro_en TEXT,
            strengths JSONB,
            weaknesses JSONB,
            research_directions JSONB,
            education JSONB,
            work_experience JSONB,
            followers INTEGER DEFAULT 0,
            views INTEGER DEFAULT 0,
            join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        # 反馈表
        """CREATE TABLE IF NOT EXISTS feedbacks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            feedback_id VARCHAR(100) UNIQUE,
            answer_id VARCHAR(100),
            rating INTEGER,
            feedback_type VARCHAR(50),
            comment TEXT,
            correction TEXT,
            student_id VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        # 时间序列表
        """CREATE TABLE IF NOT EXISTS timeseries_data (
            id SERIAL,
            table_name VARCHAR(100),
            time TIMESTAMPTZ NOT NULL,
            value DOUBLE PRECISION,
            tags JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        # 知识库表
        """CREATE TABLE IF NOT EXISTS knowledge_points (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            point_id VARCHAR(100) UNIQUE,
            course_id VARCHAR(100),
            name VARCHAR(255) NOT NULL,
            code VARCHAR(100) NOT NULL,
            description TEXT,
            parent_id VARCHAR(100),
            level INTEGER DEFAULT 1,
            sort_order INTEGER DEFAULT 0,
            status VARCHAR(20) DEFAULT 'active',
            meta_data JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        # 聊天会话表
        """CREATE TABLE IF NOT EXISTS chat_sessions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            session_id VARCHAR(100) UNIQUE,
            student_id VARCHAR(100),
            course_id VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            message_count INTEGER DEFAULT 0
        )""",
        # 聊天消息表
        """CREATE TABLE IF NOT EXISTS chat_messages (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            message_id VARCHAR(100) UNIQUE,
            session_id VARCHAR(100),
            student_id VARCHAR(100),
            role VARCHAR(20),
            content TEXT NOT NULL,
            sources JSONB,
            knowledge_point_ids JSONB,
            rating INTEGER,
            comment VARCHAR(500),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        # 聊天反馈表
        """CREATE TABLE IF NOT EXISTS chat_feedback (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            feedback_id VARCHAR(100) UNIQUE,
            message_id VARCHAR(100),
            session_id VARCHAR(100),
            rating INTEGER,
            comment VARCHAR(500),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        # 预警表
        """CREATE TABLE IF NOT EXISTS warnings (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            warning_id VARCHAR(100) UNIQUE,
            student_id VARCHAR(255) NOT NULL,
            student_name VARCHAR(255),
            warning_type VARCHAR(50) NOT NULL,
            level VARCHAR(20) NOT NULL,
            status VARCHAR(20) DEFAULT 'active',
            risk_score DOUBLE PRECISION DEFAULT 0.0,
            description TEXT,
            trigger_reason TEXT,
            suggestions TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        # 预警规则表
        """CREATE TABLE IF NOT EXISTS warning_rules (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            rule_name VARCHAR(255) NOT NULL,
            rule_type VARCHAR(50) NOT NULL,
            threshold DOUBLE PRECISION DEFAULT 0.3,
            enabled VARCHAR(10) DEFAULT 'true',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        # RAG文档表
        """CREATE TABLE IF NOT EXISTS rag_documents (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            doc_id VARCHAR(100) UNIQUE NOT NULL,
            content TEXT NOT NULL,
            doc_metadata JSONB,
            course_id VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        # RAG会话表
        """CREATE TABLE IF NOT EXISTS rag_sessions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            session_id VARCHAR(100) UNIQUE NOT NULL,
            student_id VARCHAR(100),
            query TEXT,
            answer TEXT,
            sources JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        # 向量文档表
        """CREATE TABLE IF NOT EXISTS vector_documents (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            doc_id VARCHAR(100) UNIQUE NOT NULL,
            content TEXT NOT NULL,
            doc_metadata JSONB,
            vector_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
    ]
    
    async with async_engine.begin() as conn:
        for sql in tables_sql:
            try:
                await conn.execute(text(sql))
            except Exception as e:
                print(f"Table init warning: {e}")
    
    print("All database tables created!")
    
    # Seed demo user
    from services.base.auth.main import seed_demo_user
    try:
        await seed_demo_user()
        print("Demo user seeded!")
    except Exception as e:
        print(f"Seed user warning: {e}")


@app.get("/", response_model=ResponseModel)
async def root():
    """Root endpoint."""
    return ResponseModel(
        code=200,
        message="欢迎使用AI-Agent教育平台API",
        data={
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "docs": "/docs"
        }
    )


@app.get("/health", response_model=ResponseModel)
async def health_check():
    """Health check endpoint."""
    return ResponseModel(
        code=200,
        message="服务健康",
        data={"status": "healthy"}
    )


# Register routers
app.include_router(auth_router, prefix=settings.API_PREFIX)
app.include_router(roles_router, prefix=settings.API_PREFIX)
app.include_router(registry_router, prefix=settings.API_PREFIX)
app.include_router(config_router, prefix=settings.API_PREFIX)
app.include_router(flow_router, prefix=settings.API_PREFIX)
app.include_router(scheduler_router, prefix=settings.API_PREFIX)
app.include_router(cache_router, prefix=settings.API_PREFIX)
app.include_router(collect_router, prefix=settings.API_PREFIX)
app.include_router(homework_router, prefix=settings.API_PREFIX)
app.include_router(portrait_router, prefix=settings.API_PREFIX)
app.include_router(timeseries_router, prefix=settings.API_PREFIX)
app.include_router(feedback_router, prefix=settings.API_PREFIX)
app.include_router(knowledge_router, prefix=settings.API_PREFIX)
app.include_router(graph_router, prefix=settings.API_PREFIX)
app.include_router(vector_router, prefix=settings.API_PREFIX)
app.include_router(chunk_router, prefix=settings.API_PREFIX)
app.include_router(embedding_router, prefix=settings.API_PREFIX)
app.include_router(faiss_router, prefix=settings.API_PREFIX)
app.include_router(es_router, prefix=settings.API_PREFIX)
app.include_router(query_rewrite_router, prefix=settings.API_PREFIX)
app.include_router(router_router, prefix=settings.API_PREFIX)
app.include_router(search_router, prefix=settings.API_PREFIX)
app.include_router(fusion_router, prefix=settings.API_PREFIX)
app.include_router(rerank_router, prefix=settings.API_PREFIX)
app.include_router(trimmer_router, prefix=settings.API_PREFIX)
app.include_router(rag_router, prefix=settings.API_PREFIX)
app.include_router(library_router, prefix=settings.API_PREFIX)
app.include_router(chat_router, prefix=settings.API_PREFIX)
app.include_router(annotation_router, prefix=settings.API_PREFIX)
app.include_router(evaluate_router, prefix=settings.API_PREFIX)
app.include_router(parse_router, prefix=settings.API_PREFIX)
app.include_router(exercise_router, prefix=settings.API_PREFIX)
app.include_router(warning_router, prefix=settings.API_PREFIX)
app.include_router(gateway_router, prefix=settings.API_PREFIX)
app.include_router(sync_router, prefix=settings.API_PREFIX)
app.include_router(agent_template_router, prefix=settings.API_PREFIX)
app.include_router(agent_deploy_router, prefix=settings.API_PREFIX)
app.include_router(agent_destroy_router, prefix=settings.API_PREFIX)
app.include_router(visual_router, prefix=settings.API_PREFIX)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
