#!/usr/bin/env python3
"""
RAG 系统改进验证脚本

验证内容:
1. 静态库索引加载状态
2. Cross-Encoder 重排序模型加载状态
3. 语义分块功能测试
4. 查询缓存管理器状态
5. RAGAS 评估模块可用性
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# 添加路径
sys.path.insert(0, str(Path(__file__).parent.parent))


async def verify_static_index():
    """验证静态库索引"""
    print("\n" + "=" * 60)
    print("[1/5] 验证静态库索引")
    print("=" * 60)
    
    from services.knowledge.rag.hybrid_search.static_index import StaticIndex
    
    static_index = StaticIndex()
    loaded = await static_index.load_from_disk()
    
    if loaded:
        stats = static_index.get_stats()
        print(f"✅ 静态库加载成功")
        print(f"   - 文档数量：{stats['doc_count']}")
        print(f"   - 词表大小：{stats['vocab_size']}")
        print(f"   - 内存占用：{stats['memory_usage_mb']:.2f} MB")
        print(f"   - 课程数量：{stats['course_count']}")
        
        # 测试检索
        test_query = "机器学习"
        query_vector = static_index.get_query_vector(test_query)
        results, search_stats = await static_index.search(query_vector, top_k=3)
        
        print(f"\n检索测试：'{test_query}'")
        print(f"   - 检索结果数：{len(results)}")
        print(f"   - 检索耗时：{search_stats.get('static_search_time', 0)*1000:.2f} ms")
        
        if results:
            print(f"   - Top 结果分数：{results[0]['score']:.4f}")
        
        return True
    else:
        print(f"❌ 静态库加载失败")
        return False


def verify_reranker():
    """验证 Cross-Encoder 重排序模型"""
    print("\n" + "=" * 60)
    print("[2/5] 验证 Cross-Encoder 重排序模型")
    print("=" * 60)
    
    from services.knowledge.rerank.main import rerank_model, initialize_reranker
    
    # 如果未初始化，尝试初始化
    if not rerank_model.initialized:
        print("正在初始化重排序模型...")
        try:
            initialize_reranker(model_name="bge-reranker-base")
        except Exception as e:
            print(f"模型初始化失败：{e}，使用降级模式")
    
    status = rerank_model.get_status()
    
    if status["initialized"]:
        print(f"✅ 重排序模型已加载")
        print(f"   - 模型名称：{status['model_name']}")
        print(f"   - 模型类型：{status['model_type']}")
        
        # 测试重排序
        test_query = "什么是人工智能"
        test_docs = [
            {"doc_id": "1", "content": "人工智能是模拟人类智能的技术"},
            {"doc_id": "2", "content": "机器学习是人工智能的一个分支"},
            {"doc_id": "3", "content": "今天天气很好"},
            {"doc_id": "4", "content": "深度学习用于图像识别"},
        ]
        
        results = rerank_model.rerank(test_query, test_docs, top_k=3)
        
        print(f"\n重排序测试：'{test_query}'")
        print(f"   - 重排序方法：{results[0].get('rerank_method', 'unknown')}")
        print(f"   - Top 结果分数：{results[0].get('rerank_score', 0):.4f}")
        print(f"   - Top 结果内容：{results[0]['content'][:30]}...")
        
        return True
    else:
        print(f"⚠️ 重排序模型未初始化")
        return False


def verify_semantic_chunking():
    """验证语义分块功能"""
    print("\n" + "=" * 60)
    print("[3/5] 验证语义分块功能")
    print("=" * 60)
    
    from services.knowledge.chunk.semantic_chunking import semantic_chunking
    
    # 测试文本（包含标题结构）
    test_text = """
# 第一章 机器学习基础

## 1.1 什么是机器学习

机器学习是人工智能的一个分支，它使用算法和统计模型使计算机系统从数据中学习。

机器学习的主要方法包括监督学习、无监督学习和强化学习。

### 1.1.1 监督学习

监督学习使用标记数据进行训练，目标是学习输入到输出的映射关系。

常见的监督学习算法包括线性回归、逻辑回归、支持向量机等。

### 1.1.2 无监督学习

无监督学习使用未标记数据进行训练，目标是发现数据中的隐藏模式。

常见的无监督学习算法包括聚类、降维、关联规则学习等。

## 1.2 深度学习

深度学习是机器学习的一个子领域，它使用多层神经网络来学习数据的层次化表示。

深度学习在图像识别、自然语言处理等领域取得了显著成功。
"""
    
    chunks = semantic_chunking(
        text=test_text,
        max_chunk_size=500,
        min_chunk_size=100,
        overlap_ratio=0.15,
        use_semantic_boundary=True
    )
    
    if chunks:
        print(f"✅ 语义分块成功")
        print(f"   - 分块数量：{len(chunks)}")
        print(f"   - 平均块大小：{sum(c['char_count'] for c in chunks) / len(chunks):.0f} 字符")
        
        # 显示第一个块的信息
        first_chunk = chunks[0]
        print(f"\n第一个块:")
        print(f"   - chunk_id: {first_chunk['chunk_id']}")
        print(f"   - 层级：{first_chunk['level']}")
        print(f"   - 内容开头：{first_chunk['content'][:50]}...")
        
        return True
    else:
        print(f"❌ 语义分块失败")
        return False


async def verify_query_cache():
    """验证查询缓存管理器"""
    print("\n" + "=" * 60)
    print("[4/5] 验证查询缓存管理器")
    print("=" * 60)
    
    from services.knowledge.rag.hybrid_search.cache_manager import QueryCacheManager
    import numpy as np
    
    # 创建缓存管理器
    cache_manager = QueryCacheManager(
        max_size=100,
        ttl=7200,  # 2 小时
        cleanup_interval=300
    )
    
    # 测试缓存
    test_query = "测试查询"
    test_vector = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
    
    await cache_manager.set(test_query, test_vector, course_id="test")
    
    # 测试获取
    cached_vector = await cache_manager.get(test_query, course_id="test")
    
    if cached_vector is not None:
        stats = cache_manager.get_stats()
        print(f"✅ 查询缓存管理器正常")
        print(f"   - 缓存大小：{stats['size']}")
        print(f"   - 最大容量：{stats['max_size']}")
        print(f"   - TTL: {stats['ttl']} 秒")
        print(f"   - 命中率：{stats['hit_rate']*100:.1f}%")
        
        return True
    else:
        print(f"❌ 查询缓存管理器异常")
        return False


def verify_ragas_module():
    """验证 RAGAS 评估模块"""
    print("\n" + "=" * 60)
    print("[5/5] 验证 RAGAS 评估模块")
    print("=" * 60)
    
    try:
        from services.knowledge.evaluation.ragas_evaluation import (
            evaluate_with_ragas,
            EvaluationQuestion,
            EvaluationMetrics
        )
        
        # 创建测试问题
        test_question = EvaluationQuestion(
            question="什么是机器学习？",
            answer="机器学习是人工智能的一个分支，使用算法从数据中学习。",
            contexts=[
                "机器学习是人工智能的一个分支，它使用算法和统计模型使计算机系统从数据中学习。",
                "机器学习的主要方法包括监督学习、无监督学习和强化学习。"
            ],
            ground_truth="机器学习是 AI 的子领域，通过算法从数据中学习模式和知识。"
        )
        
        # 执行评估（使用模拟模式）
        result = evaluate_with_ragas(
            questions=[test_question],
            metrics=EvaluationMetrics.ALL_METRICS
        )
        
        if "overall_score" in result:
            print(f"✅ RAGAS 评估模块可用")
            print(f"   - 总体分数：{result.get('overall_score', 0):.4f}")
            print(f"   - 评估指标：{list(result.get('metric_scores', {}).keys())}")
            
            if result.get("is_mock"):
                print(f"   - 模式：模拟评估 (RAGAS 未安装)")
            else:
                print(f"   - 模式：真实评估 (RAGAS 已安装)")
            
            return True
        else:
            print(f"❌ RAGAS 评估异常")
            return False
            
    except ImportError as e:
        print(f"❌ RAGAS 模块导入失败：{e}")
        return False
    except Exception as e:
        print(f"❌ RAGAS 评估失败：{e}")
        return False


async def main():
    """主函数"""
    print("=" * 60)
    print("RAG 系统改进验证")
    print("=" * 60)
    print(f"时间：{datetime.now().isoformat()}")
    
    results = []
    
    # 1. 静态库索引
    results.append(("静态库索引", await verify_static_index()))
    
    # 2. Cross-Encoder 重排序
    results.append(("Cross-Encoder 重排序", verify_reranker()))
    
    # 3. 语义分块
    results.append(("语义分块", verify_semantic_chunking()))
    
    # 4. 查询缓存
    results.append(("查询缓存", await verify_query_cache()))
    
    # 5. RAGAS 评估
    results.append(("RAGAS 评估", verify_ragas_module()))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("验证结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {status} - {name}")
    
    print(f"\n总计：{passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有改进验证通过！")
        return 0
    else:
        print(f"\n⚠️ {total - passed} 项验证失败，请检查日志")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
