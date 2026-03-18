#!/usr/bin/env python
"""Comprehensive API testing script."""
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
    
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        results = {}
        
        # ========== BASE SERVICES ==========
        print("\n" + "="*50)
        print("BASE SERVICES TESTING")
        print("="*50)
        
        # Auth
        print("\n--- Auth Service ---")
        response = await client.post("/api/v1/auth/login", data={"username": "demo", "password": "demo123"})
        if response.status_code == 200:
            token = response.json().get("data", {}).get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            results["auth_login"] = "PASS"
        else:
            headers = {}
            results["auth_login"] = "FAIL"
        
        # Test all base endpoints
        base_tests = [
            ("/api/v1/roles", "GET", None, "roles_list"),
            ("/api/v1/registry/services", "GET", None, "registry"),
            ("/api/v1/config", "GET", None, "config"),
            ("/api/v1/flow/status", "GET", None, "flow_status"),
            ("/api/v1/schedule/tasks", "GET", None, "schedule_tasks"),
            ("/api/v1/cache/stats", "GET", None, "cache_stats"),
        ]
        
        for path, method, data, name in base_tests:
            try:
                if method == "GET":
                    response = await client.get(path, headers=headers)
                results[name] = "PASS" if response.status_code < 500 else "FAIL"
                print(f"{name}: {response.status_code}")
            except Exception as e:
                results[name] = f"ERROR: {str(e)[:30]}"
                print(f"{name}: ERROR")
        
        # ========== DATA SERVICES ==========
        print("\n--- Data Service ---")
        data_tests = [
            ("/api/v1/collect/behavior", "POST", {"student_id": "s1", "event": "login"}, "collect_behavior"),
            ("/api/v1/collect/status", "GET", None, "collect_status"),
            ("/api/v1/homework", "GET", None, "homework_list"),
            ("/api/v1/portrait/demo-student", "GET", None, "portrait_get"),
            ("/api/v1/portrait/generate", "POST", {"student_id": "s1", "course_id": "python101"}, "portrait_generate"),
            ("/api/v1/timeseries/query", "GET", {"table": "learning_behavior", "limit": 10}, "timeseries_query"),
            ("/api/v1/feedback", "GET", None, "feedback_list"),
            ("/api/v1/feedback/submit", "POST", {"student_id": "s1", "content": "good"}, "feedback_submit"),
        ]
        
        for path, method, data, name in data_tests:
            try:
                if method == "GET":
                    response = await client.get(path, params=data if data else {}, headers=headers)
                else:
                    response = await client.post(path, json=data if data else {}, headers=headers)
                results[name] = "PASS" if response.status_code < 500 else f"FAIL({response.status_code})"
                print(f"{name}: {response.status_code}")
            except Exception as e:
                results[name] = f"ERROR"
                print(f"{name}: ERROR - {str(e)[:50]}")
        
        # ========== KNOWLEDGE SERVICES ==========
        print("\n--- Knowledge Service ---")
        knowledge_tests = [
            ("/api/v1/knowledge/points", "GET", None, "kp_list"),
            ("/api/v1/knowledge/points", "POST", {"name": "测试知识点", "code": "TEST001", "course_id": "python101"}, "kp_create"),
            ("/api/v1/knowledge/graph", "GET", None, "graph_list"),
            ("/api/v1/knowledge/vector/stats", "GET", None, "vector_stats"),
            ("/api/v1/knowledge/chunk", "GET", None, "chunk_list"),
            ("/api/v1/knowledge/faiss/stats", "GET", None, "faiss_stats"),
            ("/api/v1/knowledge/es/stats", "GET", None, "es_stats"),
            ("/api/v1/knowledge/search", "POST", {"query": "python 列表", "top_k": 3}, "search"),
            ("/api/v1/knowledge/rag/chat", "POST", {"message": "什么是列表?", "session_id": "test123"}, "rag_chat"),
            ("/api/v1/knowledge/rag/health", "GET", None, "rag_health"),
        ]
        
        for path, method, data, name in knowledge_tests:
            try:
                if method == "GET":
                    response = await client.get(path, params=data if data else {}, headers=headers)
                else:
                    response = await client.post(path, json=data if data else {}, headers=headers)
                results[name] = "PASS" if response.status_code < 500 else f"FAIL({response.status_code})"
                print(f"{name}: {response.status_code}")
            except Exception as e:
                results[name] = f"ERROR"
                print(f"{name}: ERROR - {str(e)[:50]}")
        
        # ========== INTELLIGENCE SERVICES ==========
        print("\n--- Intelligence Service ---")
        intelligence_tests = [
            ("/api/v1/intelligence/chat/message", "POST", {"student_id": "s1", "message": "你好"}, "chat_message"),
            ("/api/v1/intelligence/parse/text", "POST", {"content": "test text"}, "parse_text"),
            ("/api/v1/intelligence/evaluate/assess", "POST", {"student_id": "s1", "knowledge_point_id": "kp001"}, "evaluate_assess"),
            ("/api/v1/intelligence/exercise/generate", "POST", {"student_id": "s1", "knowledge_point_id": "kp001", "difficulty": "medium"}, "exercise_gen"),
            ("/api/v1/intelligence/warning", "GET", None, "warning_list"),
            ("/api/v1/intelligence/warning/stats", "GET", None, "warning_stats"),
            ("/api/v1/intelligence/annotation/generate", "POST", {"homework_id": "hw1", "error_type": "syntax", "error_content": "错误"}, "annotation_gen"),
        ]
        
        for path, method, data, name in intelligence_tests:
            try:
                if method == "GET":
                    response = await client.get(path, params=data if data else {}, headers=headers)
                else:
                    response = await client.post(path, json=data if data else {}, headers=headers)
                results[name] = "PASS" if response.status_code < 500 else f"FAIL({response.status_code})"
                print(f"{name}: {response.status_code}")
            except Exception as e:
                results[name] = f"ERROR"
                print(f"{name}: ERROR - {str(e)[:50]}")
        
        # ========== ADAPT SERVICES ==========
        print("\n--- Adapt Service ---")
        adapt_tests = [
            ("/api/v1/adapt/platforms", "GET", None, "platforms"),
            ("/api/v1/adapt/sync/jobs", "GET", None, "sync_jobs"),
        ]
        
        for path, method, data, name in adapt_tests:
            try:
                if method == "GET":
                    response = await client.get(path, headers=headers)
                results[name] = "PASS" if response.status_code < 500 else f"FAIL"
                print(f"{name}: {response.status_code}")
            except Exception as e:
                results[name] = f"ERROR"
                print(f"{name}: ERROR")
        
        # ========== VISUAL SERVICES ==========
        print("\n--- Visual Service ---")
        visual_tests = [
            ("/api/v1/visual/display/graph/knowledge/python101", "GET", None, "kg_display"),
            ("/api/v1/visual/display/chart/trend/student001", "GET", None, "trend_chart"),
        ]
        
        for path, method, data, name in visual_tests:
            try:
                if method == "GET":
                    response = await client.get(path, headers=headers)
                results[name] = "PASS" if response.status_code < 500 else f"FAIL"
                print(f"{name}: {response.status_code}")
            except Exception as e:
                results[name] = f"ERROR"
                print(f"{name}: ERROR")
        
        # ========== SUMMARY ==========
        print("\n" + "="*50)
        print("TEST SUMMARY")
        print("="*50)
        
        passed = sum(1 for v in results.values() if v == "PASS")
        failed = sum(1 for v in results.values() if v.startswith("FAIL"))
        errors = sum(1 for v in results.values() if v.startswith("ERROR"))
        
        print(f"Total: {len(results)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Errors: {errors}")
        
        print("\nFailed/Error endpoints:")
        for k, v in results.items():
            if v != "PASS":
                print(f"  {k}: {v}")
        
        # Save results
        with open("test_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print("\nResults saved to test_results.json")

if __name__ == "__main__":
    asyncio.run(test_all_endpoints())
