#!/usr/bin/env python3
"""
RAG F1 改进验证脚本

快速验证改进是否生效:
1. MMR lambda 参数验证
2. 融合权重验证
3. HyDE 启用状态验证
4. FAISS 参数验证
5. 重排序候选池验证
"""

import sys
from pathlib import Path

# 添加路径 (确保在导入 services 之前)
BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(Path(__file__).parent))


def test_mmr_lambda():
    """测试 MMR lambda 参数"""
    print("=" * 60)
    print("测试 1: MMR Lambda 参数")
    print("=" * 60)
    
    from services.knowledge.trimmer.main import DEFAULT_MMR_LAMBDA
    
    expected = 0.75
    actual = DEFAULT_MMR_LAMBDA
    
    if actual == expected:
        print(f"✅ PASS: MMR Lambda = {actual} (期望：{expected})")
        return True
    else:
        print(f"❌ FAIL: MMR Lambda = {actual} (期望：{expected})")
        return False


def test_fusion_weights():
    """测试融合权重配置"""
    print("\n" + "=" * 60)
    print("测试 2: 融合权重配置")
    print("=" * 60)
    
    from services.knowledge.rag.main import INTENT_WEIGHTS
    
    all_pass = True
    
    for intent, weights in INTENT_WEIGHTS.items():
        semantic_weight = weights.get("semantic", 0)
        expected_min = 0.35  # 所有意图的 semantic 权重至少 0.35
        
        if semantic_weight >= expected_min:
            print(f"✅ {intent}: semantic={semantic_weight}")
        else:
            print(f"❌ {intent}: semantic={semantic_weight} (期望>={expected_min})")
            all_pass = False
    
    return all_pass


def test_hyde_default():
    """测试 HyDE 默认启用状态"""
    print("\n" + "=" * 60)
    print("测试 3: HyDE 默认启用状态")
    print("=" * 60)
    
    import inspect
    from services.knowledge.rag.retriever import hybrid_search
    
    # 获取函数签名
    sig = inspect.signature(hybrid_search)
    enable_hyde_default = sig.parameters['enable_hyde'].default
    
    expected = True
    
    if enable_hyde_default == expected:
        print(f"✅ PASS: enable_hyde 默认值 = {enable_hyde_default}")
        return True
    else:
        print(f"❌ FAIL: enable_hyde 默认值 = {enable_hyde_default} (期望：{expected})")
        return False


def test_faiss_params():
    """测试 FAISS 参数"""
    print("\n" + "=" * 60)
    print("测试 4: FAISS HNSW 参数")
    print("=" * 60)
    
    from services.knowledge.faiss_indexer.main import HNSWConfig
    
    ef_search_expected = 100
    ef_construction_expected = 256
    
    actual_ef_search = HNSWConfig.EF_SEARCH
    actual_ef_construction = HNSWConfig.EF_CONSTRUCTION
    
    pass_count = 0
    
    if actual_ef_search == ef_search_expected:
        print(f"✅ EF_SEARCH = {actual_ef_search} (期望：{ef_search_expected})")
        pass_count += 1
    else:
        print(f"❌ EF_SEARCH = {actual_ef_search} (期望：{ef_search_expected})")
    
    if actual_ef_construction == ef_construction_expected:
        print(f"✅ EF_CONSTRUCTION = {actual_ef_construction} (期望：{ef_construction_expected})")
        pass_count += 1
    else:
        print(f"❌ EF_CONSTRUCTION = {actual_ef_construction} (期望：{ef_construction_expected})")
    
    return pass_count == 2


def test_rerank_candidate_pool():
    """测试重排序候选池扩展"""
    print("\n" + "=" * 60)
    print("测试 5: 重排序候选池扩展逻辑")
    print("=" * 60)
    
    # 读取 main.py 源代码验证
    with open("services/knowledge/rag/main.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # 检查候选池扩展
    has_candidate_pool_expansion = "request.top_k * 3" in content
    has_rerank_expansion = "rerank_top_k = min(request.top_k * 2" in content
    
    if has_candidate_pool_expansion:
        print("✅ 融合候选池扩展：top_k × 3")
    else:
        print("❌ 融合候选池扩展未找到")
    
    if has_rerank_expansion:
        print("✅ 重排序候选扩展：top_k × 2")
    else:
        print("❌ 重排序候选扩展未找到")
    
    return has_candidate_pool_expansion and has_rerank_expansion


def test_query_translation_priority():
    """测试查询翻译优先策略"""
    print("\n" + "=" * 60)
    print("测试 6: 查询翻译优先策略")
    print("=" * 60)
    
    # 读取 retriever.py 源代码验证
    with open("services/knowledge/rag/retriever.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # 检查翻译后禁用 HyDE 的逻辑
    has_translation_disable_hyde = "if translation_applied:" in content and "enable_hyde = False" in content
    
    if has_translation_disable_hyde:
        print("✅ 查询翻译后禁用 HyDE (避免双重转换)")
        return True
    else:
        print("❌ 查询翻译后禁用 HyDE 逻辑未找到")
        return False


def test_mock_embedding_eval():
    """测试 Mock Embedding 评估可用性"""
    print("\n" + "=" * 60)
    print("测试 7: Mock Embedding 评估可用性")
    print("=" * 60)
    
    import importlib.util
    
    # 检查 Mock Embedding 评估脚本是否存在
    eval_script = BACKEND_DIR / "evaluation_tools" / "mock_embedding_eval.py"
    
    if eval_script.exists():
        print(f"✅ Mock Embedding 评估脚本存在：{eval_script}")
        
        # 尝试导入模块
        spec = importlib.util.spec_from_file_location("mock_embedding_eval", eval_script)
        try:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            print("✅ Mock Embedding 评估模块可导入")
            return True
        except Exception as e:
            print(f"❌ Mock Embedding 评估模块导入失败：{e}")
            return False
    else:
        print(f"❌ Mock Embedding 评估脚本不存在：{eval_script}")
        return False


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("RAG F1 改进验证")
    print("=" * 60)

    results = []

    results.append(("MMR Lambda", test_mmr_lambda()))
    results.append(("融合权重", test_fusion_weights()))
    results.append(("HyDE 默认启用", test_hyde_default()))
    results.append(("FAISS 参数", test_faiss_params()))
    results.append(("重排序候选池", test_rerank_candidate_pool()))
    results.append(("查询翻译优先", test_query_translation_priority()))
    results.append(("Mock Embedding 评估", test_mock_embedding_eval()))

    # 汇总
    print("\n" + "=" * 60)
    print("验证汇总")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    print(f"\n总计：{passed}/{total} 通过")

    if passed == total:
        print("\n🎉 所有改进已正确应用！")
        print("\n下一步：运行 Mock Embedding 评估获取 F1 基线")
        print("命令：python evaluation_tools/mock_embedding_eval.py")
        print("\n或使用真实 RAG 服务评估：")
        print("命令：python run_full_evaluation.py")
        return 0
    else:
        print(f"\n⚠️ {total - passed} 项改进未正确应用，请检查代码")
        return 1


if __name__ == "__main__":
    sys.exit(main())
