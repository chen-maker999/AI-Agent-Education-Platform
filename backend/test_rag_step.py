"""Trace RAG processing step by step"""
import asyncio
import traceback as tb
from datetime import datetime
from common.database.postgresql import AsyncSessionLocal
from sqlalchemy import select
from services.knowledge.rag.main import RAGDocument, RAGRequest

async def test_step_by_step():
    print("Step-by-step RAG test")
    print("="*50)
    
    request = RAGRequest(
        query="hello",
        student_id="test",
        use_rewrite=False,
        use_rerank=False,
        top_k=3
    )
    
    try:
        # Step 1: Query rewrite
        print("\n[Step 1] Query rewrite...")
        expanded_queries = [request.query]
        if request.use_rewrite:
            try:
                from services.knowledge.query.main import rewrite_query
                expanded_queries = rewrite_query(request.query, request.course_id or "")
                print(f"  Expanded queries: {expanded_queries}")
            except Exception as e:
                print(f"  Query rewrite failed: {e}")
        else:
            print("  Skipped (use_rewrite=False)")
        
        # Step 2: Document retrieval
        print("\n[Step 2] Document retrieval...")
        all_results = []
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(RAGDocument).limit(10))
            docs = result.scalars().all()
        print(f"  Retrieved {len(docs)} documents")
        
        for doc in docs[:3]:
            print(f"  - {doc.doc_id}: {doc.content[:50]}...")
            all_results.append({
                "doc_id": doc.doc_id,
                "content": doc.content,
                "score": 1.0,
                "doc_metadata": doc.doc_metadata
            })
        
        # Step 3: Trim context
        print("\n[Step 3] Trim context...")
        trimmed_docs = []
        max_length = 3000
        for doc in all_results:
            content = doc.get('content', '')
            if len(content) <= max_length:
                trimmed_docs.append(doc)
        print(f"  Trimmed to {len(trimmed_docs)} documents")
        
        # Step 4: Generate answer with Kimi
        print("\n[Step 4] Generate answer with Kimi...")
        from common.integration.kimi import get_kimi_response
        
        context_text = "\n\n".join([
            f"Reference {i+1}: {d.get('content', '')[:200]}"
            for i, d in enumerate(trimmed_docs[:3])
        ])
        
        prompt = f"""Based on the following references, answer the question.

References:
{context_text}

Question: {request.query}

Answer in one sentence."""
        
        answer = await get_kimi_response(
            prompt=prompt,
            system_prompt="You are a helpful assistant. Answer concisely."
        )
        print(f"  Answer: {answer[:100]}...")
        
        # Step 5: Save session
        print("\n[Step 5] Save session...")
        new_session_id = "test_session_123"
        print(f"  Would save to session: {new_session_id}")
        
        print("\n" + "="*50)
        print("All steps completed successfully!")
        
    except Exception as e:
        print(f"\nERROR at step: {e}")
        tb.print_exc()

if __name__ == "__main__":
    asyncio.run(test_step_by_step())
