#!/usr/bin/env python3
"""
对比测试：模拟智能体流式接口的完整流程。
- 方式A: kimi_client.chat()（非流式）  ← test_vision_exam_image.py 用的是这个
- 方式B: kimi_client.chat_stream()（流式） ← streaming endpoint 用的是这个

对比两者是否都能正确识别图片。
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import json
import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from services.agent.prompts import build_agent_system_prompt, VISION_DOCUMENT_PHOTO_RULES
from common.integration.kimi import kimi_client


async def build_messages(image_path: Path, agent_type: str, enabled_tools: list):
    mime = "image/png" if image_path.suffix.lower() == ".png" else "image/jpeg"
    b64 = base64.b64encode(image_path.read_bytes()).decode("ascii")
    data_url = f"data:{mime};base64,{b64}"

    system_prompt = build_agent_system_prompt(
        agent_type=agent_type,
        custom_prompt="",
        enabled_tools=enabled_tools,
        personality="balanced",
    )
    system_prompt += "\n\n【测试模式】必须根据图像如实描述文档类型与内容。"

    return [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "请说明这张图片里是什么材料，列出可见的标题、题型结构。"},
                {"type": "image_url", "image_url": {"url": data_url, "detail": "high"}},
            ],
        },
    ]


async def test_chat(messages, model):
    print("\n=== [A] kimi_client.chat() ===")
    result = await kimi_client.chat(
        messages=messages, model=model, temperature=1.0, max_tokens=2048, top_p=1.0
    )
    if "error" in result:
        print("ERROR:", result.get("error"), result.get("detail", "")[:300])
        return None
    choices = result.get("choices") or []
    return (choices[0].get("message") or {}).get("content", "") if choices else ""


async def test_chat_stream(messages, model):
    print("\n=== [B] kimi_client.chat_stream() ===")
    chunks = []
    async for chunk in kimi_client.chat_stream(
        messages=messages, model=model, temperature=1.0, max_tokens=2048, top_p=1.0
    ):
        if chunk.startswith("data: "):
            data_str = chunk[6:]
            if data_str == "[DONE]":
                break
            try:
                parsed = json.loads(data_str)
                if parsed.get("error"):
                    print("STREAM ERROR:", parsed["error"])
                    break
                delta = parsed.get("choices", [{}])[0].get("delta", {})
                if isinstance(delta, dict):
                    content = delta.get("content", "")
                else:
                    content = str(delta)
                sys.stdout.write(content)
                sys.stdout.flush()
                chunks.append(content)
            except (json.JSONDecodeError, KeyError):
                pass
    print()
    return "".join(chunks)


def summarize(text: str):
    if not text:
        return "(空)"
    if len(text) > 300:
        return text[:300] + "..."
    return text


async def main() -> int:
    parser = argparse.ArgumentParser(description="对比 chat vs chat_stream 图片识别")
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--agent-type", default="explorer")
    parser.add_argument("--model", default="kimi-k2.5")
    args = parser.parse_args()

    p = args.image.expanduser().resolve()
    if not p.is_file():
        print(f"ERROR: {p} not found", file=sys.stderr)
        return 2

    print(f"Image: {p} ({p.stat().st_size} bytes)")
    print(f"Model: {args.model}  AgentType: {args.agent_type}")
    print(f"VPR length: {len(VISION_DOCUMENT_PHOTO_RULES)}")

    if not kimi_client.api_key:
        print("ERROR: KIMI_API_KEY not set", file=sys.stderr)
        return 3

    enabled_tools = ["reading", "tavily_search", "knowledge_search", "delegate_task"]
    messages = await build_messages(p, args.agent_type, enabled_tools)

    # 打印消息结构（仅结构，不打印 base64 内容）
    for i, m in enumerate(messages):
        c = m.get("content", "")
        if isinstance(c, str):
            print(f"  msg[{i}] role={m['role']} content_len={len(c)}")
        elif isinstance(c, list):
            for j, b in enumerate(c):
                if isinstance(b, dict) and b.get("type") == "image_url":
                    url = b.get("image_url", {}).get("url", "")
                    print(f"  msg[{i}] role={m['role']} block[{j}] type=image_url url_len={len(url)}")
                elif isinstance(b, dict):
                    txt = b.get("text", "")[:80]
                    print(f"  msg[{i}] role={m['role']} block[{j}] type=text preview='{txt}'")
                else:
                    print(f"  msg[{i}] role={m['role']} block[{j}] type=unknown")

    # 方式A
    text_a = await test_chat(messages, args.model)
    print("\n[A] 结果:", summarize(text_a))

    # 方式B
    text_b = await test_chat_stream(messages, args.model)
    print("[B] 结果:", summarize(text_b))

    # 对比
    if text_a and text_b:
        same = text_a.strip() == text_b.strip()
        print(f"\n{'[相同]' if same else '[不同]'} chat vs chat_stream 结果")
    return 0


if __name__ == "__main__":
    import sys as _sys
    for s in (_sys.stdout, _sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except Exception:
            pass
    raise SystemExit(asyncio.run(main()))
