#!/usr/bin/env python3
"""
静态库索引预构建脚本

用途:
- 预计算 TF-IDF 静态库索引
- 加速检索 (50ms→10ms)
- 磁盘持久化，支持快速加载

使用方法:
    python scripts/build_static_index.py
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# 添加路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.knowledge.rag.hybrid_search.static_index import StaticIndex
from common.database.postgresql import AsyncSessionLocal
from sqlalchemy import select
from services.knowledge.rag.main import RAGDocument


async def load_documents_from_db(course_id: str = None) -> List[Dict[str, Any]]:
    """从数据库加载文档"""
    async with AsyncSessionLocal() as session:
        if course_id:
            result = await session.execute(
                select(RAGDocument.doc_id, RAGDocument.content, RAGDocument.course_id)
                .where(RAGDocument.course_id == course_id)
            )
        else:
            result = await session.execute(
                select(RAGDocument.doc_id, RAGDocument.content, RAGDocument.course_id)
            )
        
        rows = result.all()
        
        documents = []
        for row in rows:
            documents.append({
                "doc_id": row.doc_id,
                "content": row.content,
                "course_id": row.course_id or "default"
            })
        
        return documents


async def build_static_index():
    """构建静态库索引"""
    print("=" * 60)
    print("静态库索引预构建")
    print("=" * 60)
    
    start_time = datetime.now()
    
    # 1. 从数据库加载文档
    print("\n[1/3] 从数据库加载文档...")
    documents = await load_documents_from_db()
    
    if not documents:
        print("⚠️ 未找到文档，请先上传文档到数据库")
        return False
    
    print(f"✅ 加载成功：{len(documents)} 个文档")
    
    # 2. 重建静态库
    print("\n[2/3] 重建静态库索引...")
    static_index = StaticIndex()
    
    success = await static_index.rebuild(documents)
    
    if not success:
        print("❌ 静态库重建失败")
        return False
    
    print(f"✅ 重建成功：{static_index.doc_count} 个文档，词表大小：{static_index.vocab_size}")
    
    # 3. 验证加载
    print("\n[3/3] 验证静态库加载...")
    new_static_index = StaticIndex()
    loaded = await new_static_index.load_from_disk()
    
    if not loaded:
        print("❌ 静态库加载验证失败")
        return False
    
    print(f"✅ 加载验证成功：{new_static_index.doc_count} 个文档")
    
    # 打印统计信息
    stats = new_static_index.get_stats()
    print("\n" + "=" * 60)
    print("静态库统计信息")
    print("=" * 60)
    print(f"文档数量：{stats['doc_count']}")
    print(f"词表大小：{stats['vocab_size']}")
    print(f"已加载：{stats['loaded']}")
    print(f"最后重建时间：{stats['last_rebuild']}")
    print(f"课程数量：{stats['course_count']}")
    print(f"内存占用：{stats['memory_usage_mb']:.2f} MB")
    
    processing_time = (datetime.now() - start_time).total_seconds()
    print(f"\n总耗时：{processing_time:.2f} 秒")
    print("=" * 60)
    
    # 测试检索
    print("\n检索测试...")
    test_query = "机器学习"
    query_vector = new_static_index.get_query_vector(test_query)
    results, search_stats = await new_static_index.search(query_vector, top_k=5)
    
    print(f"查询：{test_query}")
    print(f"检索结果数：{len(results)}")
    print(f"检索耗时：{search_stats.get('static_search_time', 0)*1000:.2f} ms")
    
    if results:
        print("\nTop 3 结果:")
        for i, r in enumerate(results[:3]):
            print(f"  [{i+1}] 分数：{r['score']:.4f}, 内容：{r['content'][:50]}...")
    
    print("\n✅ 静态库索引预构建完成")
    return True


async def main():
    """主函数"""
    try:
        success = await build_static_index()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 构建失败：{e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
