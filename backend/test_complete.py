#!/usr/bin/env python
"""Complete API testing script - all endpoints."""
import sys
import os
import asyncio
import httpx
import json

sys.path.insert(0, r"D:\AI-Agent-Education-Platform-cursor\backend")
os.environ.setdefault("PYTHONPATH", r"D:\AI-Agent-Education-Platform-cursor\backend")

async def test_all_endpoints():
    """Test all registered endpoints comprehensively."""
    base_url = "http://localhost:8000"
    
    # Wait for server
    print("Waiting for backend...")
    for i in range(15):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{base_url}/health", timeout=5.0)
                if response.status_code == 200:
                    print("Backend is ready!")
                    break
        except:
            pass
        await asyncio.sleep(2)
    else:
        print("Backend not ready!")
        return
    
    # Login first
    print("\n=== Login ===")
    async with httpx.AsyncClient(base_url=base_url, timeout=60.0) as client:
        response = await client.post("/api/v1/auth/login", data={"username": "demo", "password": "demo123"})
        if response.status_code == 200:
            token = response.json().get("data", {}).get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            print("Login successful!")
        else:
            headers = {}
            print(f"Login failed: {response.status_code}")
            return
        
        # ========== TEST ALL MAJOR ENDPOINTS ==========
        results = {}
        
        # 1. BASE SERVICES
        print("\n" + "="*60)
        print("1. BASE SERVICES TESTING")
        print("="*60)
        
        base_tests = [
            # Auth
            ("GET", "/api/v1/auth/me", None, "auth_me"),
            ("GET", "/api/v1/roles", None, "roles_list"),
            ("GET", "/api/v1/registry/services", None, "registry_services"),
            ("GET", "/api/v1/config", None, "config_list"),
            ("GET", "/api/v1/flow/status", None, "flow_status"),
            ("GET", "/api/v1/schedule/tasks", None, "schedule_tasks"),
            ("GET", "/api/v1/cache/stats", None, "cache_stats"),
        ]
        
        for method, path, data, name in base_tests:
            try:
                if method == "GET":
                    response = await client.get(path, headers=headers)
                else:
                    response = await client.post(path, json=data, headers=headers)
                results[name] = "PASS" if response.status_code < 400 else f"FAIL({response.status_code})"
                if response.status_code >= 400:
                    print(f"{name}: {response.status_code} - {response.text[:200]}")
                else:
                    print(f"{name}: {response.status_code}")
            except Exception as e:
                results[name] = f"ERROR"
                print(f"{name}: ERROR - {str(e)}")
        
        # 2. DATA SERVICES
        print("\n" + "="*60)
        print("2. DATA SERVICES TESTING")
        print("="*60)
        
        data_tests = [
            ("POST", "/api/v1/collect/behavior", {"student_id": "s1", "event": "login", "timestamp": "2026-03-16T10:00:00Z"}, "collect_behavior"),
            ("GET", "/api/v1/collect/status", None, "collect_status"),
            ("POST", "/api/v1/homework/upload", None, "homework_upload"),  # Skip - needs file
            ("GET", "/api/v1/homework", None, "homework_list"),
            ("GET", "/api/v1/portrait/student_001", None, "portrait_get"),
            ("POST", "/api/v1/portrait/generate", {"student_id": "s1"}, "portrait_generate"),
            ("POST", "/api/v1/timeseries/write", {"table": "test", "data": [{"t": "2026-03-16", "v": 1}]}, "timeseries_write"),
            ("GET", "/api/v1/timeseries/query?table=test&limit=10", None, "timeseries_query"),
            ("GET", "/api/v1/feedback", None, "feedback_list"),
            ("POST", "/api/v1/feedback/submit", {"student_id": "s1", "content": "good"}, "feedback_submit"),
        ]
        
        for method, path, data, name in data_tests:
            if data is None and method == "GET":
                try:
                    response = await client.get(path, headers=headers)
                    results[name] = "PASS" if response.status_code < 400 else f"FAIL({response.status_code})"
                    if response.status_code >= 400:
                        print(f"{name}: {response.status_code} - {response.text[:200]}")
                    else:
                        print(f"{name}: {response.status_code}")
                except Exception as e:
                    results[name] = "ERROR"
                    print(f"{name}: ERROR - {str(e)}")
            elif data is not None:
                try:
                    response = await client.post(path, json=data, headers=headers)
                    results[name] = "PASS" if response.status_code < 400 else f"FAIL({response.status_code})"
                    if response.status_code >= 400:
                        print(f"{name}: {response.status_code} - {response.text[:200]}")
                    else:
                        print(f"{name}: {response.status_code}")
                except Exception as e:
                    results[name] = "ERROR"
                    print(f"{name}: ERROR - {str(e)}")
        
        # 3. KNOWLEDGE SERVICES
        print("\n" + "="*60)
        print("3. KNOWLEDGE SERVICES TESTING")
        print("="*60)
        
        knowledge_tests = [
            ("POST", "/api/v1/knowledge/points", {"name": "Python列表", "code": "PY001", "course_id": "python101"}, "kp_create"),
            ("GET", "/api/v1/knowledge/points", None, "kp_list"),
            ("GET", "/api/v1/knowledge/graph", None, "graph_list"),
            ("POST", "/api/v1/graph/nodes", {"name": "TestNode", "type": "concept"}, "graph_node_create"),
            ("GET", "/api/v1/knowledge/vector/stats", None, "vector_stats"),
            ("GET", "/api/v1/knowledge/chunk", None, "chunk_list"),
            ("POST", "/api/v1/chunk/text", {"content": "test content", "chunk_size": 500}, "chunk_create"),
            ("POST", "/api/v1/embedding/encode", {"texts": ["hello", "world"]}, "embedding_encode"),
            ("GET", "/api/v1/knowledge/faiss/stats", None, "faiss_stats"),
            ("POST", "/api/v1/faiss/search", {"query": "test", "top_k": 3}, "faiss_search"),
            ("GET", "/api/v1/knowledge/es/stats", None, "es_stats"),
            ("POST", "/api/v1/elasticsearch/search", {"query": "test"}, "es_search"),
            ("POST", "/api/v1/query/rewrite", {"query": "python list"}, "query_rewrite"),
            ("POST", "/api/v1/router/intent", {"query": "什么是列表"}, "router_intent"),
            ("POST", "/api/v1/search/multi", {"query": "python"}, "search_multi"),
            ("POST", "/api/v1/fusion/combine", {"results": [[{"text": "a", "score": 0.9}, {"text": "b", "score": 0.8}]]}, "fusion_combine"),
            ("POST", "/api/v1/rerank/rerank", {"query": "test", "documents": [{"text": "doc1"}, {"text": "doc2"}]}, "rerank"),
            ("POST", "/api/v1/context/trim", {"context": ["text1", "text2"], "max_tokens": 1000}, "context_trim"),
            ("POST", "/api/v1/rag/chat", {"session_id": "s1", "student_id": "st1", "message": "hello"}, "rag_chat"),
            ("GET", "/api/v1/rag/documents", None, "rag_docs"),
        ]
        
        for method, path, data, name in knowledge_tests:
            try:
                if method == "GET":
                    response = await client.get(path, headers=headers)
                else:
                    response = await client.post(path, json=data, headers=headers)
                results[name] = "PASS" if response.status_code < 400 else f"FAIL({response.status_code})"
                print(f"{name}: {response.status_code}")
            except Exception as e:
                results[name] = "ERROR"
                print(f"{name}: ERROR")
        
        # 4. INTELLIGENCE SERVICES
        print("\n" + "="*60)
        print("4. INTELLIGENCE SERVICES TESTING")
        print("="*60)
        
        intelligence_tests = [
            ("POST", "/api/v1/chat/message", {"student_id": "s1", "message": "你好"}, "chat_message"),
            ("GET", "/api/v1/chat/history/test123", None, "chat_history"),
            ("POST", "/api/v1/chat/feedback", {"message_id": "m1", "session_id": "s1", "rating": 5}, "chat_feedback"),
            ("POST", "/api/v1/parse/text", {"content": "test text"}, "parse_text"),
            ("POST", "/api/v1/parse/code/syntax", {"code": "print('hello')", "language": "python"}, "parse_code"),
            ("POST", "/api/v1/evaluate/mastery", {"student_id": "s1", "knowledge_point_id": "kp1", "correct": True, "difficulty": 0.5}, "eval_mastery"),
            ("GET", "/api/v1/evaluate/weakness/s1", None, "eval_weakness"),
            ("GET", "/api/v1/evaluate/strength/s1", None, "eval_strength"),
            ("GET", "/api/v1/evaluate/summary/s1", None, "eval_summary"),
            ("POST", "/api/v1/exercise/generate", {"student_id": "s1", "knowledge_point_id": "kp1", "difficulty": "medium"}, "exercise_gen"),
            ("GET", "/api/v1/warning", None, "warning_list"),
            ("GET", "/api/v1/warning/stats", None, "warning_stats"),
            ("POST", "/api/v1/warning/rules", {"rule": "test", "threshold": 0.5}, "warning_rules"),
            ("POST", "/api/v1/annotation/generate", {"homework_id": "hw1", "error_type": "syntax"}, "annotation_gen"),
        ]
        
        for method, path, data, name in intelligence_tests:
            try:
                if method == "GET":
                    response = await client.get(path, headers=headers)
                else:
                    response = await client.post(path, json=data, headers=headers)
                results[name] = "PASS" if response.status_code < 400 else f"FAIL({response.status_code})"
                print(f"{name}: {response.status_code}")
            except Exception as e:
                results[name] = "ERROR"
                print(f"{name}: ERROR")
        
        # 5. ADAPT SERVICES
        print("\n" + "="*60)
        print("5. ADAPT SERVICES TESTING")
        print("="*60)
        
        adapt_tests = [
            ("GET", "/api/v1/adapt/gateway/platforms", None, "adapt_platforms"),
            ("GET", "/api/v1/adapt/sync/jobs", None, "adapt_sync_jobs"),
        ]
        
        for method, path, data, name in adapt_tests:
            try:
                response = await client.get(path, headers=headers)
                results[name] = "PASS" if response.status_code < 400 else f"FAIL({response.status_code})"
                print(f"{name}: {response.status_code}")
            except Exception as e:
                results[name] = "ERROR"
                print(f"{name}: ERROR")
        
        # 6. VISUAL SERVICES
        print("\n" + "="*60)
        print("6. VISUAL SERVICES TESTING")
        print("="*60)
        
        visual_tests = [
            ("POST", "/api/v1/visual/chart", {"type": "line", "data": {"x": [1,2,3], "y": [1,2,3]}}, "visual_chart"),
            ("GET", "/api/v1/visual/portrait", None, "visual_portrait"),
            ("GET", "/api/v1/visual/error-distribution?course_id=python101", None, "visual_errors"),
            ("GET", "/api/v1/visual/timeseries?student_id=s1", None, "visual_timeseries"),
        ]
        
        for method, path, data, name in visual_tests:
            try:
                if method == "GET":
                    response = await client.get(path, headers=headers)
                else:
                    response = await client.post(path, json=data, headers=headers)
                results[name] = "PASS" if response.status_code < 400 else f"FAIL({response.status_code})"
                print(f"{name}: {response.status_code}")
            except Exception as e:
                results[name] = "ERROR"
                print(f"{name}: ERROR")
        
        # ========== SUMMARY ==========
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        passed = sum(1 for v in results.values() if v == "PASS")
        failed = sum(1 for v in results.values() if v.startswith("FAIL"))
        errors = sum(1 for v in results.values() if v.startswith("ERROR"))
        
        print(f"\nTotal: {len(results)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Errors: {errors}")
        print(f"Success Rate: {passed/len(results)*100:.1f}%")
        
        print("\n=== DETAILED RESULTS ===")
        for k, v in sorted(results.items()):
            status = "OK" if v == "PASS" else "FAIL"
            print(f"[{status}] {k}: {v}")
        
        # Save results
        with open("test_complete_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print("\nResults saved to test_complete_results.json")

if __name__ == "__main__":
    asyncio.run(test_all_endpoints())
