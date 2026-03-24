#!/usr/bin/env python3
"""
重新构建 BM25 索引

从数据库加载所有 RAG 文档，重建 BM25 索引
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


async def rebuild_bm25_index():
    """从数据库重新构建 BM25 索引"""
    from sqlalchemy import select
    from common.database.postgresql import AsyncSessionLocal
    from services.knowledge.rag.main import RAGDocument
    from services.knowledge.bm25_search.main import BM25Index, BM25Document
    
    print("="*60)
    print("重新构建 BM25 索引")
    print("="*60)
    
    # 创建新的 BM25 索引
    bm25_index = BM25Index()
    
    # 从数据库加载文档
    print("\n从数据库加载 RAG 文档...")
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(RAGDocument))
        docs = result.scalars().all()
    
    print(f"找到 {len(docs)} 个文档")
    
    # 添加到 BM25 索引
    print("\n构建 BM25 索引...")
    for i, doc in enumerate(docs):
        bm25_doc = BM25Document(
            doc_id=doc.doc_id,
            content=doc.content,
            course_id=doc.course_id,
            metadata=doc.doc_metadata or {}
        )
        bm25_index.add_document(bm25_doc)
        
        if (i + 1) % 500 == 0:
            print(f"  已处理 {i + 1}/{len(docs)} 个文档")
    
    # 保存索引
    print("\n保存索引到磁盘...")
    bm25_index.save()
    
    print(f"\n索引构建完成:")
    print(f"  - 文档总数：{bm25_index.total_docs}")
    print(f"  - 词表大小：{len(bm25_index.vocabulary)}")
    print(f"  - 平均文档长度：{bm25_index.avg_doc_length:.2f}")
    print(f"  - 索引文件：data/bm25_index.pkl")
    
    # 测试检索
    print("\n测试检索:")
    test_queries = ["继承", "inheritance", "多态", "polymorphism"]
    for query in test_queries:
        results = bm25_index.search(query, top_k=3)
        print(f"  查询 '{query}': {len(results)} 个结果")
        if results:
            print(f"    Top-1: score={results[0]['score']:.4f}, doc_id={results[0]['doc_id'][:20]}...")


if __name__ == "__main__":
    asyncio.run(rebuild_bm25_index())
