#!/usr/bin/env python
"""Comprehensive API testing script - test all routes."""
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
    
    # Get all routes
    from main import app
    routes = {}
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            path = route.path
            methods = list(route.methods) if route.methods else ['GET']
            for method in methods:
                routes[f"{method} {path}"] = {"path": path, "method": method}
    
    # Filter out health, docs, openapi
    api_routes = {k: v for k, v in routes.items() 
                  if not k.startswith('GET /') or (not k.endswith('/health') and 
                  not k.startswith('GET /docs') and not k.startswith('GET /openapi') and 
                  not k.startswith('GET /redoc') and k != 'GET /')}
    
    print(f"\nFound {len(api_routes)} API routes to test")
    
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        results = {}
        
        # Login first to get token
        print("\nLogging in...")
        response = await client.post("/api/v1/auth/login", data={"username": "demo", "password": "demo123"})
        if response.status_code == 200:
            token = response.json().get("data", {}).get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            print("Login successful!")
        else:
            headers = {}
            print("Login failed!")
        
        # Test all routes
        print(f"\nTesting {len(api_routes)} endpoints...")
        
        for route_key, route_info in api_routes.items():
            path = route_info["path"]
            method = route_info["method"]
            
            try:
                if method == "GET":
                    response = await client.get(path, headers=headers, params={})
                elif method == "POST":
                    response = await client.post(path, headers=headers, json={})
                elif method == "PUT":
                    response = await client.put(path, headers=headers, json={})
                elif method == "DELETE":
                    response = await client.delete(path, headers=headers)
                elif method == "PATCH":
                    response = await client.patch(path, headers=headers, json={})
                else:
                    continue
                
                if response.status_code < 500:
                    results[route_key] = f"PASS ({response.status_code})"
                else:
                    results[route_key] = f"FAIL ({response.status_code})"
                    
                # Only print failures
                if response.status_code >= 400:
                    print(f"{route_key}: {response.status_code}")
                    
            except Exception as e:
                error_msg = str(e)[:50]
                results[route_key] = f"ERROR"
                print(f"{route_key}: ERROR - {error_msg}")
        
        # ========== SUMMARY ==========
        print("\n" + "="*50)
        print("TEST SUMMARY")
        print("="*50)
        
        passed = sum(1 for v in results.values() if v.startswith("PASS"))
        failed = sum(1 for v in results.values() if v.startswith("FAIL"))
        errors = sum(1 for v in results.values() if v.startswith("ERROR"))
        
        print(f"Total: {len(results)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Errors: {errors}")
        
        # Save results
        with open("test_all_routes.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print("\nResults saved to test_all_routes.json")

if __name__ == "__main__":
    asyncio.run(test_all_endpoints())
