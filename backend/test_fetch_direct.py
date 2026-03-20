"""直接测试 fetch_url_document，不走 HTTP"""
import os
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import asyncio
import sys
sys.path.insert(0, '.')

class FakeForm:
    def __init__(self, data):
        self._data = data
    def __getitem__(self, key):
        return self._data[key]

async def test():
    from services.knowledge.rag.main import fetch_url_document
    try:
        result = await fetch_url_document(
            url="https://arxiv.org/pdf/1706.03762.pdf",
            course_id="test_transformer"
        )
        print("SUCCESS:", result)
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(test())
