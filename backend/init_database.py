"""
初始化数据库表脚本
使用方法：python init_database.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text
from common.database.postgresql import async_engine

async def init_database():
    """初始化数据库表"""
    
    tables_sql = [
        # RAG 文档表
        """CREATE TABLE IF NOT EXISTS rag_documents (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            doc_id VARCHAR(100) UNIQUE NOT NULL,
            content TEXT NOT NULL,
            doc_metadata JSONB,
            course_id VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        # RAG 会话表
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
        # 知识库表 (knowledge_bases)
        """CREATE TABLE IF NOT EXISTS knowledge_bases (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            kb_id VARCHAR(100) UNIQUE,
            owner_id VARCHAR(100),
            name VARCHAR(255) NOT NULL,
            description TEXT,
            settings JSONB DEFAULT '{}'::jsonb,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
    ]
    
    async with async_engine.begin() as conn:
        for i, sql in enumerate(tables_sql):
            try:
                await conn.execute(text(sql))
                print(f"[{i+1}/{len(tables_sql)}] 创建表成功：{sql.split('IF NOT EXISTS ')[1].split(' ')[0] if 'IF NOT EXISTS' in sql else 'unknown'}")
            except Exception as e:
                print(f"[{i+1}/{len(tables_sql)}] 创建表失败：{e}")
    
    print("\n数据库表初始化完成!")

if __name__ == "__main__":
    asyncio.run(init_database())
