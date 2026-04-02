#!/usr/bin/env python3
"""
本地验证：将试卷/文档类图片以 image_url 发给 Kimi，检查是否识别为文档而非「简单标志图」。

用法（在项目 backend 目录下）:
  python scripts/test_vision_exam_image.py --image "C:/path/to/exam.png"
  python scripts/test_vision_exam_image.py --image ./fixtures/exam.png

依赖: 环境变量 KIMI_API_KEY（或 .env）
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import sys
from pathlib import Path

# 保证可导入 backend 包
_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from services.agent.prompts import build_agent_system_prompt, VISION_DOCUMENT_PHOTO_RULES


USER_PROMPT = "请说明这张图片里是什么材料，列出可见的标题、题型结构；不要说是简单文字图或 Logo。"


def _configure_stdio_utf8() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass


async def main() -> int:
    _configure_stdio_utf8()
    parser = argparse.ArgumentParser(description="Test Kimi vision on exam/document photo")
    parser.add_argument("--image", required=True, type=Path, help="Path to PNG/JPEG file")
    parser.add_argument("--agent-type", default="tutor", help="tutor | explorer | general")
    args = parser.parse_args()

    p = args.image.expanduser().resolve()
    if not p.is_file():
        print(f"ERROR: file not found: {p}", file=sys.stderr)
        return 2

    raw = p.read_bytes()
    suffix = p.suffix.lower()
    mime = "image/png" if suffix == ".png" else "image/jpeg" if suffix in (".jpg", ".jpeg") else "image/png"
    b64 = base64.b64encode(raw).decode("ascii")
    data_url = f"data:{mime};base64,{b64}"

    from common.integration.kimi import kimi_client

    if not kimi_client.api_key:
        print("ERROR: KIMI_API_KEY 未配置，无法调用 API", file=sys.stderr)
        return 3

    system = build_agent_system_prompt(
        agent_type=args.agent_type,
        custom_prompt="",
        enabled_tools=[],
        personality="balanced",
    )
    # build_agent_system_prompt 已含 VISION_DOCUMENT_PHOTO_RULES；再强调一次测试目标
    system += "\n\n【测试模式】必须根据图像如实描述文档类型与内容。"

    messages = [
        {"role": "system", "content": system},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": USER_PROMPT},
                {"type": "image_url", "image_url": {"url": data_url, "detail": "high"}},
            ],
        },
    ]

    print(f"Image: {p} ({len(raw)} bytes, {mime})")
    print(f"VISION_DOCUMENT_PHOTO_RULES len: {len(VISION_DOCUMENT_PHOTO_RULES)} chars")
    print("--- calling kimi-k2.5 ---")

    result = await kimi_client.chat(
        messages=messages,
        model="kimi-k2.5",
        temperature=1.0,
        max_tokens=2048,
        top_p=1.0,
    )

    if "error" in result:
        print("API error:", result.get("error"), result.get("detail", "")[:500], file=sys.stderr)
        return 4

    choices = result.get("choices") or []
    text = (choices[0].get("message") or {}).get("content", "") if choices else ""
    print("\n=== MODEL RESPONSE ===\n")
    print(text or "(empty)")

    bad_phrases = ("简单", "标志", "logo", "Logo", "仅为", "过于简单")
    hits = [x for x in bad_phrases if x in text]
    if hits:
        print(f"\n[警告] 回复中含可能被用户视为敷衍的措辞: {hits}", file=sys.stderr)

    good_hints = ("试卷", "考试", "填空", "数学", "高等数学", "题", "分")
    if any(g in text for g in good_hints):
        print("\n[通过] 回复中出现与试卷/题目相关的关键词。")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
