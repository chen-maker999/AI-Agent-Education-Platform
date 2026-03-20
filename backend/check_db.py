"""直接查询数据库中的文档"""
import asyncio
from sqlalchemy import select
from common.database.postgresql import AsyncSessionLocal
from services.knowledge.rag.main import RAGDocument

async def check_docs():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(RAGDocument).limit(20))
        docs = result.scalars().all()
        print(f"数据库中的文档数量: {len(docs)}")
        for doc in docs[:5]:
            print(f"  - doc_id: {doc.doc_id}, course_id: {doc.course_id}, content: {doc.content[:50]}...")

asyncio.run(check_docs())
