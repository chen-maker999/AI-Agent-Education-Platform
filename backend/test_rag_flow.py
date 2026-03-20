"""测试RAG完整流程：创建知识库、上传文件、知识库问答"""

import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"

def test_rag_flow():
    print("=" * 60)
    print("开始测试RAG完整流程")
    print("=" * 60)
    
    # 1. 创建知识库
    print("\n[1] 创建知识库...")
    kb_data = {
        "owner_id": "test_user",
        "name": "DeepSORT论文知识库",
        "description": "用于测试的DeepSORT目标跟踪论文知识库",
        "settings": {"top_k": 5, "use_rewrite": True, "use_rerank": True}
    }
    
    response = requests.post(f"{BASE_URL}/knowledge/library", json=kb_data)
    print(f"创建知识库响应状态: {response.status_code}")
    
    if response.status_code == 200:
        kb_result = response.json()
        print(f"创建知识库成功: {json.dumps(kb_result, ensure_ascii=False, indent=2)}")
        kb_id = kb_result.get("data", {}).get("kb_id")
    else:
        print(f"创建知识库失败: {response.text}")
        kb_id = "test_kb"  # 使用默认ID继续测试
    
    # 2. 上传PDF文件
    print("\n[2] 上传PDF文件...")
    pdf_path = r"D:\AI-Agent-Education-Platform-cursor\papers\deepsort.pdf"
    
    with open(pdf_path, "rb") as f:
        files = {"file": ("deepsort.pdf", f, "application/pdf")}
        data = {"course_id": kb_id}
        response = requests.post(f"{BASE_URL}/knowledge/rag/upload", files=files, data=data)
    
    print(f"上传文件响应状态: {response.status_code}")
    print(f"上传文件响应: {response.text}")
    
    if response.status_code == 200:
        upload_result = response.json()
        print(f"上传成功! 共 {upload_result.get('data', {}).get('doc_count', 0)} 个文档块")
    else:
        print(f"上传失败: {response.text}")
    
    # 等待文档处理
    print("\n等待文档处理...")
    time.sleep(3)  # Wait longer
    
    # 3. 查看已上传的文档
    print("\n[3] 查看已上传的文档...")
    response = requests.get(f"{BASE_URL}/knowledge/rag/documents", params={"course_id": kb_id})
    docs_data = response.json()
    print(f"文档列表响应: {docs_data.get('data', {}).get('total', 0)} 个文档")
    
    # 4. 进行知识库问答
    print("\n[4] 进行知识库问答...")
    
    # 测试问题
    test_queries = [
        "什么是DeepSORT算法?",
        "DeepSORT的目标跟踪流程是什么?",
        "DeepSORT和SORT有什么区别?"
    ]
    
    for query in test_queries:
        print(f"\n--- 询问: {query} ---")

        # 使用 'default' 作为 course_id
        chat_data = {
            "query": query,
            "student_id": "test_user",
            "session_id": "test_session",
            "course_id": "default",
            "use_rewrite": True,
            "use_rerank": True,
            "top_k": 5
        }
        
        response = requests.post(f"{BASE_URL}/knowledge/rag/chat", json=chat_data)
        print(f"问答响应状态: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            answer = result.get('answer', 'N/A')
            print(f"回答: {answer[:200]}..." if len(answer) > 200 else f"回答: {answer}")
            print(f"来源数量: {len(result.get('sources', []))}")
        else:
            print(f"问答失败: {response.status_code}")
        
        time.sleep(1)
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    test_rag_flow()
