import os
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import asyncio
import sys
sys.path.insert(0, ".")

async def main():
    from common.database.postgresql import AsyncSessionLocal
    from services.knowledge.rag.main import RAGDocument
    from sqlalchemy import select, func

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(func.count(RAGDocument.id)))
        total = result.scalar()
        print(f"Total documents in rag_documents: {total}")

        result = await session.execute(
            select(RAGDocument.course_id, func.count(RAGDocument.id))
            .group_by(RAGDocument.course_id)
            .order_by(RAGDocument.course_id)
        )
        print("\nBy course_id:")
        for row in result:
            print(f"  {row[0]}: {row[1]} chunks")

        result = await session.execute(
            select(RAGDocument)
            .order_by(RAGDocument.doc_id)
            .limit(3)
        )
        print("\nFirst 3 docs:")
        for doc in result.scalars():
            meta = doc.doc_metadata or {}
            print(f"  filename={meta.get('filename')}, course_id={doc.course_id}, content_len={len(doc.content)}")
            print(f"    preview: {repr(doc.content[:80])}")

asyncio.run(main())
