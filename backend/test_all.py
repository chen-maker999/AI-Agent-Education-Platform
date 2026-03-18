#!/usr/bin/env python
"""Complete API test - all endpoints."""
import asyncio
import httpx

async def test():
    base_url = 'http://localhost:8000'
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        # Login
        r = await client.post('/api/v1/auth/login', data={'username': 'demo', 'password': 'demo123'})
        if r.status_code != 200:
            print("Login failed!")
            return
        token = r.json()['data']['access_token']
        h = {'Authorization': f'Bearer {token}'}
        
        # All tests
        tests = [
            # BASE SERVICES
            ("GET", "/api/v1/auth/me", None, "auth_me"),
            ("GET", "/api/v1/roles", None, "roles_list"),
            ("GET", "/api/v1/registry/services", None, "registry"),
            ("GET", "/api/v1/config", None, "config"),
            ("GET", "/api/v1/flow/status", None, "flow_status"),
            ("GET", "/api/v1/schedule/tasks", None, "schedule_tasks"),
            ("GET", "/api/v1/cache/stats", None, "cache_stats"),
            
            # KNOWLEDGE - Points
            ("POST", "/api/v1/knowledge/points", {"name": "Test", "code": "T001", "course_id": "c1"}, "kp_create"),
            ("GET", "/api/v1/knowledge/points", None, "kp_list"),
            ("GET", "/api/v1/knowledge/points/schema", None, "kp_schema"),
            
            # KNOWLEDGE - Graph
            ("GET", "/api/v1/knowledge/graph", None, "kg_list"),
            ("POST", "/api/v1/graph/nodes", {"name": "test", "type": "concept"}, "kg_node"),
            
            # KNOWLEDGE - Vector
            ("GET", "/api/v1/knowledge/vector/stats", None, "vector_stats"),
            ("POST", "/api/v1/vector/documents", {"text": "test", "metadata": {}}, "vector_add"),
            
            # KNOWLEDGE - Chunk
            ("GET", "/api/v1/knowledge/chunk", None, "chunk_list"),
            ("POST", "/api/v1/chunk/text", {"content": "test content", "chunk_size": 500}, "chunk_create"),
            
            # KNOWLEDGE - Embedding
            ("POST", "/api/v1/embedding/encode", {"texts": ["hello"]}, "embedding"),
            
            # KNOWLEDGE - FAISS
            ("GET", "/api/v1/knowledge/faiss/stats", None, "faiss_stats"),
            ("POST", "/api/v1/faiss/search", {"query": "test", "top_k": 3}, "faiss_search"),
            
            # KNOWLEDGE - ES
            ("GET", "/api/v1/knowledge/es/stats", None, "es_stats"),
            ("POST", "/api/v1/elasticsearch/search", {"query": "test"}, "es_search"),
            
            # KNOWLEDGE - Search
            ("POST", "/api/v1/search/multi", {"query": "python"}, "search_multi"),
            ("POST", "/api/v1/query/rewrite", {"query": "python list"}, "query_rewrite"),
            ("POST", "/api/v1/router/intent", {"query": "什么是列表"}, "router"),
            ("POST", "/api/v1/fusion/combine", {"results": [[{"text": "a", "score": 0.9}]]}, "fusion"),
            ("POST", "/api/v1/rerank/rerank", {"query": "test", "documents": [{"text": "doc1"}]}, "rerank"),
            ("POST", "/api/v1/context/trim", {"context": ["a", "b"], "max_tokens": 100}, "trim"),
            
            # RAG
            ("POST", "/api/v1/rag/chat", {"session_id": "s1", "student_id": "st1", "message": "hello"}, "rag_chat"),
            ("GET", "/api/v1/rag/documents", None, "rag_docs"),
            
            # INTELLIGENCE - Chat
            ("POST", "/api/v1/chat/message", {"student_id": "s1", "message": "你好"}, "chat_message"),
            ("GET", "/api/v1/chat/history/test123", None, "chat_history"),
            ("POST", "/api/v1/chat/feedback", {"message_id": "m1", "session_id": "s1", "rating": 5}, "chat_feedback"),
            
            # INTELLIGENCE - Parse
            ("POST", "/api/v1/parse/text", {"content": "test"}, "parse_text"),
            ("POST", "/api/v1/parse/code/syntax", {"code": "print(1)", "language": "python"}, "parse_syntax"),
            
            # INTELLIGENCE - Evaluate
            ("POST", "/api/v1/evaluate/mastery", {"student_id": "s1", "knowledge_point_id": "kp1", "correct": True}, "eval_mastery"),
            ("GET", "/api/v1/evaluate/weakness/s1", None, "eval_weakness"),
            ("GET", "/api/v1/evaluate/strength/s1", None, "eval_strength"),
            ("GET", "/api/v1/evaluate/summary/s1", None, "eval_summary"),
            
            # INTELLIGENCE - Exercise
            ("POST", "/api/v1/exercise/generate", {"student_id": "s1", "knowledge_point_id": "kp1", "difficulty": "medium"}, "exercise_gen"),
            
            # INTELLIGENCE - Warning
            ("GET", "/api/v1/warning", None, "warning_list"),
            ("GET", "/api/v1/warning/stats", None, "warning_stats"),
            
            # INTELLIGENCE - Annotation
            ("POST", "/api/v1/annotation/generate", {"homework_id": "hw1", "error_type": "syntax"}, "annotation"),
            
            # DATA - Collect
            ("POST", "/api/v1/collect/behavior", {"student_id": "s1", "event": "login"}, "collect_behavior"),
            ("GET", "/api/v1/collect/status", None, "collect_status"),
            
            # DATA - Homework
            ("GET", "/api/v1/homework", None, "homework_list"),
            
            # DATA - Portrait
            ("GET", "/api/v1/portrait/student_001", None, "portrait"),
            ("POST", "/api/v1/portrait/generate", {"student_id": "s1"}, "portrait_gen"),
            
            # DATA - Timeseries
            ("POST", "/api/v1/timeseries/write", {"table": "test", "data": [{"t": "2026-01-01", "v": 1}]}, "ts_write"),
            ("GET", "/api/v1/timeseries/query?table=test&limit=10", None, "ts_query"),
            
            # DATA - Feedback
            ("GET", "/api/v1/feedback", None, "feedback_list"),
            ("POST", "/api/v1/feedback/submit", {"student_id": "s1", "content": "good"}, "feedback_submit"),
            
            # ADAPT
            ("GET", "/api/v1/adapt/gateway/platforms", None, "adapt_platforms"),
            ("GET", "/api/v1/adapt/sync/jobs", None, "adapt_sync"),
            
            # VISUAL
            ("POST", "/api/v1/visual/chart", {"type": "line", "data": {"x": [1], "y": [1]}}, "visual_chart"),
            ("GET", "/api/v1/visual/portrait", None, "visual_portrait"),
            ("GET", "/api/v1/visual/error-distribution?course_id=c1", None, "visual_errors"),
            ("GET", "/api/v1/visual/timeseries?student_id=s1", None, "visual_ts"),
        ]
        
        ok = []
        fail = []
        
        for method, path, data, name in tests:
            try:
                if method == "GET":
                    r = await client.get(path, headers=h)
                else:
                    r = await client.post(path, json=data, headers=h)
                
                if r.status_code < 400:
                    ok.append(f"{name}: {r.status_code}")
                else:
                    fail.append(f"{name}: {r.status_code}")
            except Exception as e:
                fail.append(f"{name}: ERROR")
        
        print("=" * 60)
        print("✅ 正常工作的接口:")
        print("=" * 60)
        for item in ok:
            print(f"  ✓ {item}")
        
        print(f"\n总计: {len(ok)} 个正常")
        
        print("\n" + "=" * 60)
        print("❌ 不能正常工作的接口:")
        print("=" * 60)
        for item in fail:
            print(f"  ✗ {item}")
        
        print(f"\n总计: {len(fail)} 个异常")

asyncio.run(test())
