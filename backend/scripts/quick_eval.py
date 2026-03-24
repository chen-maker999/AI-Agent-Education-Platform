#!/usr/bin/env python3
"""
RAG 快速评估脚本

支持多种评估模式：
- mock: Mock Embedding + Mock LLM（最快，无需 RAG 服务）
- pytest: 运行 pytest 测试（验证代码正确性）
- full: 完整评估（需要 RAG 服务）

使用示例:
    # 快速评估（默认 103 样本，Mock 模式）
    python scripts/quick_eval.py
    
    # 快速测试（10 样本）
    python scripts/quick_eval.py --fast
    
    # 运行 pytest 测试
    python scripts/quick_eval.py --pytest
    
    # 指定样本数
    python scripts/quick_eval.py --samples 50
"""

import asyncio
import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime

# 添加路径
BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))


def run_mock_evaluation(samples: int = 103) -> dict:
    """运行 Mock Embedding 评估"""
    print("=" * 60)
    print(f"Mock Embedding 评估（{samples} 样本）")
    print("=" * 60)
    
    eval_script = BACKEND_DIR / "evaluation_tools" / "mock_embedding_eval.py"
    
    cmd = [
        sys.executable,
        str(eval_script),
        "--max-samples", str(samples),
        "--output", str(BACKEND_DIR / "evaluation_tools" / "quick_eval_report.json")
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # 打印输出
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    
    # 加载报告
    report_path = BACKEND_DIR / "evaluation_tools" / "quick_eval_report.json"
    if report_path.exists():
        with open(report_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def run_pytest_tests() -> int:
    """运行 pytest 测试"""
    print("=" * 60)
    print("运行 pytest 测试")
    print("=" * 60)
    
    cmd = [
        sys.executable,
        "-m", "pytest",
        str(BACKEND_DIR / "tests"),
        "-v",
        "--tb=short"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # 打印输出
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    
    return result.returncode


def run_full_evaluation(samples: int = 10) -> dict:
    """运行完整评估（需要 RAG 服务）"""
    print("=" * 60)
    print(f"完整评估（{samples} 样本，需要 RAG 服务）")
    print("=" * 60)
    
    eval_script = BACKEND_DIR / "run_full_evaluation.py"
    
    cmd = [
        sys.executable,
        str(eval_script),
        "--max-samples", str(samples)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # 打印输出
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    
    return {}


def print_quick_summary(report: dict):
    """打印快速评估摘要"""
    if not report:
        return
    
    print("\n" + "=" * 60)
    print("快速评估摘要")
    print("=" * 60)
    
    metrics = report.get("metrics", {})
    f1 = metrics.get("F1", {})
    
    print(f"样本数：{report.get('sample_count', 'N/A')}")
    print(f"耗时：{report.get('total_time_seconds', 'N/A')}秒")
    print()
    print("核心指标:")
    print(f"  F1:      {f1.get('mean', 'N/A')} (中位数：{f1.get('median', 'N/A')})")
    print(f"  Precision: {metrics.get('Precision', {}).get('mean', 'N/A')}")
    print(f"  Recall:    {metrics.get('Recall', {}).get('mean', 'N/A')}")
    
    # 与基线对比
    baseline_f1 = 0.5715
    current_f1 = f1.get('mean', 0)
    
    print()
    print(f"基线对比 (基线 F1={baseline_f1}):")
    if current_f1 >= baseline_f1:
        improvement = ((current_f1 - baseline_f1) / baseline_f1) * 100
        print(f"  ✅ F1 提升：+{improvement:.1f}%")
    else:
        degradation = ((baseline_f1 - current_f1) / baseline_f1) * 100
        print(f"  ⚠️ F1 下降：-{degradation:.1f}%")
    
    print("=" * 60)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="RAG 快速评估脚本")
    parser.add_argument(
        "--mode",
        choices=["mock", "pytest", "full"],
        default="mock",
        help="评估模式：mock（最快）/ pytest（测试）/ full（完整）"
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="快速模式（仅 10 样本）"
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=None,
        help="样本数（默认：mock=103, pytest=N/A, full=10）"
    )
    parser.add_argument(
        "--output",
        default=None,
        help="输出报告路径"
    )
    
    args = parser.parse_args()
    
    # 确定样本数
    if args.samples:
        samples = args.samples
    elif args.fast:
        samples = 10
    else:
        samples = {"mock": 103, "pytest": 0, "full": 10}.get(args.mode, 103)
    
    start_time = datetime.now()
    
    if args.mode == "mock":
        # Mock Embedding 评估
        report = run_mock_evaluation(samples=samples)
        print_quick_summary(report)
        
        # 保存摘要
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"\n报告已保存：{args.output}")
        
        return 0
    
    elif args.mode == "pytest":
        # Pytest 测试
        exit_code = run_pytest_tests()
        
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"\n总耗时：{elapsed:.2f}秒")
        
        if exit_code == 0:
            print("\n✅ 所有测试通过！")
        else:
            print(f"\n❌ 测试失败，退出码：{exit_code}")
        
        return exit_code
    
    elif args.mode == "full":
        # 完整评估
        report = run_full_evaluation(samples=samples)
        print_quick_summary(report)
        return 0
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
