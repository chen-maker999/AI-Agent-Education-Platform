"""Benchmark: image homework grading (Kimi vision + Pillow overlay)."""

from __future__ import annotations

import asyncio
import pathlib
import sys
import time

# backend/ as cwd
BACKEND = pathlib.Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from services.data.homework_review.main import (  # noqa: E402
    draw_grade_marks_on_image,
    kimi_grade_homework_image,
    normalize_homework_image_bytes,
)


async def main() -> None:
    candidates = [
        BACKEND
        / "data"
        / "agent_workspace"
        / "chat_1774664493795"
        / "20260328102133_微信图片_20260327095809_269_90.jpg",
        pathlib.Path(
            r"C:\Users\31897\.cursor\projects\d-AI-Agent-Education-Platform-cursor\assets"
            r"\c__Users_31897_AppData_Roaming_Cursor_User_workspaceStorage_6962fbb6b8610aea227179da9d009cb2_images______20260327095809_269_90-4e5d6d05-bec0-4f62-a4d1-e98bdb954dac.png"
        ),
    ]
    img_path = next((p for p in candidates if p.is_file()), None)
    if not img_path:
        print("No benchmark image found.")
        sys.exit(1)

    raw = img_path.read_bytes()
    print(f"file: {img_path.name}")
    print(f"raw_size: {len(raw)} bytes")

    t0 = time.perf_counter()
    nb, mime = normalize_homework_image_bytes(raw)
    t1 = time.perf_counter()
    print(f"normalize_homework_image_bytes: {(t1 - t0) * 1000:.1f} ms (out {len(nb)} bytes, {mime})")

    t0 = time.perf_counter()
    result = await kimi_grade_homework_image(nb, mime)
    t_kimi = time.perf_counter() - t0
    print(f"kimi_grade_homework_image: {t_kimi:.2f} s")

    if result.get("error"):
        print("kimi error:", result.get("error"))
        if result.get("detail"):
            print("detail:", str(result.get("detail"))[:500])
        sys.exit(2)

    marks = result.get("marks") or []
    print(f"score: {result.get('score')}, marks: {len(marks)}, issues: {len(result.get('issues') or [])}")

    t0 = time.perf_counter()
    out_png = draw_grade_marks_on_image(nb, marks)
    t_draw = time.perf_counter() - t0
    print(f"draw_grade_marks_on_image: {t_draw * 1000:.1f} ms (png {len(out_png)} bytes)")

    print(f"total_wall (norm+kimi+draw): {t_kimi + t_draw + 0.001:.2f} s (excl. norm)")


if __name__ == "__main__":
    asyncio.run(main())
