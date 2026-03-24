#!/usr/bin/env python3
"""
预构建静态库索引脚本

用途:
- 从数据库加载所有稳定文档
- 构建 TF-IDF 静态库索引
- 保存到磁盘供快速检索使用

使用方法:
    cd backend
    source .venv/bin/activate
    python build_static_index.py
"""

import asyncio
import sys
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select
from common.database.postgresql import AsyncSessionLocal
from services.knowledge.rag.main import RAGDocument
from services.knowledge.rag.hybrid_search.static_index import StaticIndex


async def build_static_index():
    """从数据库加载文档并构建静态库索引"""
    print("=" * 60)
    print("开始构建静态库索引")
    print("=" * 60)
    
    try:
        # 从数据库加载所有文档
        print("\n[1/4] 正在从数据库加载文档...")
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(RAGDocument))
            docs = result.scalars().all()
        
        if not docs:
            print("❌ 数据库中没有文档，无法构建静态库")
            return False
        
        print(f"✓ 加载成功：{len(docs)} 个文档")
        
        # 准备文档数据
        print("\n[2/4] 正在准备文档数据...")
        documents = [
            {
                'doc_id': doc.doc_id,
                'content': doc.content,
                'course_id': doc.course_id or 'default'
            }
            for doc in docs
        ]
        print(f"✓ 准备完成：{len(documents)} 个文档")
        
        # 构建静态库
        print("\n[3/4] 正在构建 TF-IDF 索引...")
        static_index = StaticIndex()
        success = await static_index.rebuild(documents)
        
        if not success:
            print("❌ 静态库构建失败")
            return False
        
        print(f"✓ 索引构建完成：{static_index.doc_count} 个文档，词表大小：{static_index.vocab_size}")
        
        # 验证加载
        print("\n[4/4] 正在验证索引加载...")
        static_index2 = StaticIndex()
        loaded = await static_index2.load_from_disk()
        
        if loaded:
            print(f"✓ 索引加载验证成功：{static_index2.doc_count} 个文档")
        else:
            print("⚠ 索引加载验证失败，但文件已保存")
        
        print("\n" + "=" * 60)
        print("✅ 静态库索引构建完成!")
        print("=" * 60)
        print(f"\n存储位置:")
        print(f"  - 模型文件：data/tfidf_static_model.pkl")
        print(f"  - 矩阵文件：data/tfidf_static_matrix.dat")
        print(f"\n统计信息:")
        print(f"  - 文档数量：{static_index.doc_count}")
        print(f"  - 词表大小：{static_index.vocab_size}")
        print(f"  - 构建时间：{static_index.last_rebuild}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 构建失败：{e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(build_static_index())
    sys.exit(0 if success else 1)
