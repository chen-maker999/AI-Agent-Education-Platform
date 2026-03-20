"""直接调用 fetch_url_document 下载论文入库"""
import os
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import asyncio
import sys
sys.path.insert(0, ".")

PAPERS = [
    ("https://arxiv.org/pdf/1706.03762.pdf", "transformer_attention_is_all_you_need"),
    ("https://arxiv.org/pdf/1812.08928.pdf", "bert_pre_training"),
    ("https://arxiv.org/pdf/2005.14165.pdf", "gpt3_language_models"),
]

async def main():
    from services.knowledge.rag.main import fetch_url_document
    for url, course_id in PAPERS:
        print(f"Fetching {url} -> {course_id}")
        try:
            r = await fetch_url_document(url=url, course_id=course_id)
            fn = r["data"]["filename"]
            cnt = r["data"]["doc_count"]
            print(f"  SUCCESS: {fn}, {cnt} chunks")
        except Exception as e:
            print(f"  ERROR: {type(e).__name__}: {e}")

asyncio.run(main())
