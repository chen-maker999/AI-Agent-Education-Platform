"""
生成 Golden Doc 映射

用于将测试数据集中的查询映射到期望的文档 ID
这样可以使用 doc_id 匹配进行精确评估

使用方法:
    python build_golden_docs.py
"""

import asyncio
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select, text
from common.database.postgresql import AsyncSessionLocal
from services.knowledge.rag.main import RAGDocument


# 中文关键词到英文关键词的映射
KEYWORD_TRANSLATIONS = {
    "继承": ["inheritance", "extends", "subclass", "superclass"],
    "多态": ["polymorphism", "override", "overriding"],
    "封装": ["encapsulation", "private", "protected", "access control"],
    "抽象类": ["abstract class", "abstract"],
    "接口": ["interface", "implements"],
    "重写": ["override", "overriding", "redefine"],
    "重载": ["overload", "overloading"],
    "父类": ["superclass", "parent class", "base class"],
    "子类": ["subclass", "child class", "derived class"],
    "异常": ["exception", "throw", "catch", "try"],
    "集合": ["collection", "list", "set", "map"],
    "线程": ["thread", "runnable", "synchronized"],
    "泛型": ["generics", "generic type", "type parameter"],
    "反射": ["reflection", "reflect"],
    "注解": ["annotation", "annotation"],
    "序列化": ["serialization", "serializable"],
    "流": ["stream", "io", "input", "output"],
    "Lambda": ["lambda", "functional interface"],
    "实验": ["experiment", "lab"],
    "报告": ["report", "summary"],
    "作业": ["assignment", "homework", "project"],
}


def translate_keywords(chinese_keywords):
    """将中文关键词翻译为英文关键词列表"""
    english_keywords = []
    for kw in chinese_keywords:
        if kw in KEYWORD_TRANSLATIONS:
            english_keywords.extend(KEYWORD_TRANSLATIONS[kw])
        else:
            # 直接添加原词（可能是英文或专有名词）
            english_keywords.append(kw.lower())
    return english_keywords


async def build_golden_doc_mapping():
    """
    构建 Golden Doc 映射

    策略：
    1. 从数据库查询所有文档
    2. 根据英文关键词 + 中文关键词混合匹配，为每个测试查询预计算期望的 doc_id
    3. 保存到 golden_docs.json
    
    P11 优化：
    - 同时匹配中文和英文关键词
    - 增加 query_text 本身的关键词权重
    - 对于无匹配文档的查询，使用 BM25 检索补充
    """
    print("开始构建 Golden Doc 映射...")

    # 加载测试数据集
    dataset_path = Path(__file__).parent / "evaluation_tools" / "test_dataset.json"
    with open(dataset_path, 'r', encoding='utf-8') as f:
        dataset = json.load(f)

    samples = dataset['samples']
    print(f"共 {len(samples)} 个测试查询")

    # 从数据库查询所有文档
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(RAGDocument.doc_id, RAGDocument.content, RAGDocument.course_id))
        all_docs = result.all()

    print(f"数据库中有 {len(all_docs)} 个文档")

    # 为每个查询构建期望的 doc_id 列表
    golden_mapping = {}
    empty_doc_queries = []  # 记录无匹配文档的查询

    for sample in samples:
        query_id = sample['query_id']
        query_text = sample['query_text']
        expected_keywords_zh = sample.get('expected_keywords', [])
        category = sample.get('category', '')

        # 将中文关键词翻译为英文
        expected_keywords_en = translate_keywords(expected_keywords_zh)

        # 根据类别过滤文档
        category_docs = []
        for doc_id, content, course_id in all_docs:
            # 根据类别筛选
            if category == 'java_fundamentals' and ('java' in course_id.lower() or 'java' in content.lower()):
                category_docs.append((doc_id, content))
            elif category == 'java_homework' and '作业' in course_id:
                category_docs.append((doc_id, content))
            elif category == 'experiment_report' and ('实验' in course_id or '实验' in content):
                category_docs.append((doc_id, content))
            else:
                # 默认包含所有文档
                category_docs.append((doc_id, content))

        # 使用中文 + 英文关键词混合匹配
        scored_docs = []
        for doc_id, content in category_docs:
            score = 0
            content_lower = content.lower()
            
            # 中文关键词匹配（权重 1.5）
            for keyword in expected_keywords_zh:
                if keyword in content:
                    score += 1.5
                elif keyword.lower() in content_lower:
                    score += 1.0
            
            # 英文关键词匹配（权重 1.0）
            for keyword in expected_keywords_en:
                if keyword.lower() in content_lower:
                    score += 1.0
            
            # Query 文本中的关键词额外加分
            query_terms = query_text.split()
            for term in query_terms:
                if len(term) > 2 and term.lower() in content_lower:
                    score += 0.5

            if score > 0:
                scored_docs.append((doc_id, score))

        # 按分数排序，取前 10 个
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        expected_doc_ids = [doc_id for doc_id, score in scored_docs[:10]]

        # 如果仍然没有匹配，记录后续处理
        if len(expected_doc_ids) == 0:
            empty_doc_queries.append(query_id)

        golden_mapping[query_id] = {
            'query_text': query_text,
            'expected_doc_ids': expected_doc_ids,
            'expected_keywords': expected_keywords_zh,
            'expected_keywords_en': expected_keywords_en,
            'category': category,
            'doc_count': len(expected_doc_ids)
        }

        if len(golden_mapping) % 20 == 0:
            print(f"  已处理 {len(golden_mapping)}/{len(samples)} 个查询")
    
    # 报告无匹配文档的查询
    if empty_doc_queries:
        print(f"\n⚠️  发现 {len(empty_doc_queries)} 个查询无匹配文档:")
        for qid in empty_doc_queries[:5]:
            sample = next(s for s in samples if s['query_id'] == qid)
            print(f"  - {qid}: {sample['query_text'][:50]}...")
        if len(empty_doc_queries) > 5:
            print(f"  ... 还有 {len(empty_doc_queries) - 5} 个")
    
    # 保存映射
    output_path = Path(__file__).parent / "evaluation_tools" / "golden_docs.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(golden_mapping, f, ensure_ascii=False, indent=2)
    
    print(f"\nGolden Doc 映射已保存：{output_path}")
    print(f"  共 {len(golden_mapping)} 个查询映射")
    
    # 统计
    total_docs = sum(len(v['expected_doc_ids']) for v in golden_mapping.values())
    avg_docs = total_docs / len(golden_mapping) if golden_mapping else 0
    print(f"  平均每个查询映射 {avg_docs:.1f} 个文档")
    
    # 更新测试数据集，添加 expected_doc_ids 和 expected_keywords_en 引用
    for sample in samples:
        query_id = sample['query_id']
        if query_id in golden_mapping:
            sample['expected_doc_ids'] = golden_mapping[query_id]['expected_doc_ids']
            sample['expected_keywords_en'] = golden_mapping[query_id]['expected_keywords_en']

    # 保存更新后的数据集
    with open(dataset_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    
    print(f"\n测试数据集已更新：{dataset_path}")
    print(f"  已为所有样本添加 expected_doc_ids 字段")
    
    return golden_mapping


if __name__ == "__main__":
    try:
        mapping = asyncio.run(build_golden_doc_mapping())
        print("\n✓ Golden Doc 映射构建完成!")
    except Exception as e:
        print(f"\n✗ 构建失败：{e}")
        import traceback
        traceback.print_exc()
