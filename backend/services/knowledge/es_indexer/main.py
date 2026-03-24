"""Elasticsearch索引 (ES-INDEXER) - 关键词检索"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib
import json

router = APIRouter(prefix="/elasticsearch", tags=["Elasticsearch Indexer"])


@router.get("/", response_model=dict)
async def get_es_stats():
    """获取Elasticsearch状态"""
    return {"code": 200, "message": "success", "data": {"status": "ok", "service": "elasticsearch indexer"}}


@router.get("/stats", response_model=dict)
async def get_es_stats_alias():
    """获取Elasticsearch统计信息"""
    return {
        "code": 200,
        "message": "success",
        "data": {
            "available": es_available,
            "index_name": INDEX_NAME,
            "storage_type": "elasticsearch" if es_available else "memory",
            "document_count": len(es_fallback_storage),
            "service": "elasticsearch"
        }
    }


# Elasticsearch客户端
es_client = None
es_available = False

# 索引名称
INDEX_NAME = "edu_knowledge"

# 索引映射配置
INDEX_MAPPING = {
    "mappings": {
        "properties": {
            "doc_id": {"type": "keyword"},
            "title": {"type": "text", "analyzer": "ik_smart", "boost": 2.0},
            "content": {"type": "text", "analyzer": "ik_smart"},
            "course_id": {"type": "keyword"},
            "knowledge_points": {"type": "keyword"},
            "content_type": {"type": "keyword"},
            "embedding_id": {"type": "keyword"},
            "created_at": {"type": "date"},
            "updated_at": {"type": "date"}
        }
    },
    "settings": {
        "number_of_shards": 3,
        "number_of_replicas": 1,
        "analysis": {
            "analyzer": {
                "ik_smart": {
                    "type": "standard"
                }
            }
        }
    }
}

# 内存存储（ES不可用时的降级方案）
es_fallback_storage: Dict[str, Dict] = {}


class ESDocument(BaseModel):
    """ES文档"""
    doc_id: str
    title: str = ""
    content: str
    course_id: Optional[str] = None
    knowledge_points: List[str] = []
    content_type: str = "text"
    metadata: Dict[str, Any] = {}


class ESIndexRequest(BaseModel):
    """索引请求"""
    documents: List[ESDocument]


class ESSearchRequest(BaseModel):
    """搜索请求"""
    query: str
    course_id: Optional[str] = None
    content_type: Optional[str] = None
    knowledge_points: Optional[List[str]] = None
    top_k: int = 10


def init_elasticsearch() -> bool:
    """初始化Elasticsearch客户端"""
    global es_client, es_available
    
    try:
        from elasticsearch import Elasticsearch
        from common.core.config import settings
        
        # 使用配置中的用户名和密码
        es_url = settings.get_elasticsearch_url()
        
        # 判断是否使用 HTTPS
        use_https = "https://" in es_url.lower()
        
        # 构建客户端参数
        client_kwargs = {
            "hosts": [es_url],
            "request_timeout": 30,
            "max_retries": 3,
            "retry_on_timeout": True
        }
        
        # 如果使用 HTTPS，需要禁用 SSL 验证（自签名证书）
        if use_https:
            client_kwargs["verify_certs"] = False
            client_kwargs["ssl_show_warn"] = False
        
        es_client = Elasticsearch(**client_kwargs)
        
        # 测试连接
        if es_client.ping():
            es_available = True
            print("Elasticsearch连接成功")
            return True
        else:
            print("Elasticsearch连接失败，使用内存存储")
            return False
    except ImportError:
        print("Elasticsearch客户端未安装，使用内存存储")
        return False
    except Exception as e:
        print(f"Elasticsearch初始化失败: {e}，使用内存存储")
        return False


def create_index() -> bool:
    """创建索引"""
    global es_client, es_available
    
    if not es_available:
        return False
    
    try:
        if not es_client.indices.exists(index=INDEX_NAME):
            es_client.indices.create(index=INDEX_NAME, body=INDEX_MAPPING)
            print(f"索引 {INDEX_NAME} 创建成功")
        return True
    except Exception as e:
        print(f"创建索引失败: {e}")
        return False


async def index_documents(documents: List[ESDocument]) -> Dict:
    """索引文档"""
    global es_client, es_available, es_fallback_storage
    
    indexed_count = 0
    
    if es_available:
        try:
            bulk_data = []
            for doc in documents:
                bulk_data.append({"index": {"_index": INDEX_NAME, "_id": doc.doc_id}})
                bulk_data.append({
                    "doc_id": doc.doc_id,
                    "title": doc.title,
                    "content": doc.content,
                    "course_id": doc.course_id,
                    "knowledge_points": doc.knowledge_points,
                    "content_type": doc.content_type,
                    "embedding_id": hashlib.md5(doc.content.encode()).hexdigest()[:16],
                    "created_at": datetime.utcnow().isoformat(),
                    "metadata": doc.metadata
                })
            
            if bulk_data:
                es_client.bulk(body=bulk_data, refresh=True)
                indexed_count = len(documents)
        except Exception as e:
            print(f"ES批量索引失败: {e}")
    else:
        # 使用内存存储
        for doc in documents:
            es_fallback_storage[doc.doc_id] = {
                "doc_id": doc.doc_id,
                "title": doc.title,
                "content": doc.content,
                "course_id": doc.course_id,
                "knowledge_points": doc.knowledge_points,
                "content_type": doc.content_type,
                "created_at": datetime.utcnow().isoformat(),
                "metadata": doc.metadata
            }
            indexed_count += 1
    
    return {
        "indexed_count": indexed_count,
        "total_docs": len(documents),
        "storage": "elasticsearch" if es_available else "memory"
    }


async def search_documents(request: ESSearchRequest) -> List[Dict]:
    """搜索文档"""
    global es_client, es_available, es_fallback_storage
    
    results = []
    
    if es_available:
        try:
            # 构建查询
            must = []
            should = []
            
            # 全文搜索
            must.append({
                "multi_match": {
                    "query": request.query,
                    "fields": ["title^2", "content"],
                    "type": "best_fields"
                }
            })
            
            # 过滤条件
            if request.course_id:
                must.append({"term": {"course_id": request.course_id}})
            
            if request.content_type:
                must.append({"term": {"content_type": request.content_type}})
            
            if request.knowledge_points:
                should.append({
                    "terms": {"knowledge_points": request.knowledge_points}
                })
            
            query = {
                "query": {
                    "bool": {
                        "must": must,
                        "should": should if should else []
                    }
                },
                "size": request.top_k,
                "highlight": {
                    "fields": {
                        "title": {},
                        "content": {"fragment_size": 150, "number_of_fragments": 3}
                    }
                }
            }
            
            response = es_client.search(index=INDEX_NAME, body=query)
            
            for hit in response["hits"]["hits"]:
                source = hit["_source"]
                results.append({
                    "doc_id": source.get("doc_id"),
                    "title": source.get("title"),
                    "content": source.get("content"),
                    "score": hit["_score"],
                    "highlights": hit.get("highlight", {}),
                    "course_id": source.get("course_id"),
                    "knowledge_points": source.get("knowledge_points", [])
                })
                
        except Exception as e:
            print(f"ES搜索失败: {e}")
    
    # 降级到内存搜索
    if not results:
        results = await fallback_search(request)
    
    return results


async def fallback_search(request: ESSearchRequest) -> List[Dict]:
    """内存降级搜索"""
    global es_fallback_storage
    
    results = []
    query_lower = request.query.lower()
    
    for doc_id, doc in es_fallback_storage.items():
        # 过滤条件
        if request.course_id and doc.get("course_id") != request.course_id:
            continue
        if request.content_type and doc.get("content_type") != request.content_type:
            continue
        
        # 简单的关键词匹配
        score = 0
        if query_lower in doc.get("title", "").lower():
            score += 2
        if query_lower in doc.get("content", "").lower():
            score += 1
        
        if score > 0:
            results.append({
                "doc_id": doc["doc_id"],
                "title": doc.get("title"),
                "content": doc.get("content"),
                "score": score,
                "highlights": {},
                "course_id": doc.get("course_id"),
                "knowledge_points": doc.get("knowledge_points", [])
            })
    
    # 排序
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:request.top_k]


async def delete_document(doc_id: str) -> bool:
    """删除文档"""
    global es_client, es_available, es_fallback_storage

    if es_available:
        try:
            es_client.delete(index=INDEX_NAME, id=doc_id, ignore=[404])
            return True
        except Exception as e:
            print(f"ES删除失败: {e}")

    if doc_id in es_fallback_storage:
        del es_fallback_storage[doc_id]
        return True

    return False


async def delete_es_documents_by_filename(filename: str) -> int:
    """按文件名删除 ES 文档"""
    global es_client, es_available, es_fallback_storage

    deleted_count = 0

    if es_available:
        try:
            # 使用 match 查询找到所有匹配的文档
            query = {"query": {"match": {"doc_id": filename}}}
            result = es_client.search(index=INDEX_NAME, body=query, size=1000)
            hits = result.get("hits", {}).get("hits", [])
            for hit in hits:
                es_client.delete(index=INDEX_NAME, id=hit["_id"], ignore=[404])
                deleted_count += 1
        except Exception as e:
            print(f"ES按文件名删除失败: {e}")

    # 也删除 fallback 存储中的匹配项
    keys_to_delete = [k for k in es_fallback_storage.keys() if filename in k]
    for key in keys_to_delete:
        del es_fallback_storage[key]
        deleted_count += 1

    return deleted_count


@router.post("/index", status_code=201)
async def index_documents_endpoint(request: ESIndexRequest):
    """索引文档接口"""
    result = await index_documents(request.documents)
    
    return {
        "code": 201,
        "message": f"成功索引 {result['indexed_count']} 个文档",
        "data": result
    }


@router.post("/search")
async def search_documents_endpoint(request: ESSearchRequest):
    """搜索文档接口"""
    results = await search_documents(request)
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "query": request.query,
            "results": results,
            "total": len(results),
            "storage": "elasticsearch" if es_available else "memory"
        }
    }


@router.delete("/documents/{doc_id}")
async def delete_document_endpoint(doc_id: str):
    """删除文档"""
    success = await delete_document(doc_id)
    
    return {
        "code": 200 if success else 404,
        "message": "删除成功" if success else "文档不存在"
    }


@router.get("/status")
async def get_status():
    """获取ES状态"""
    return {
        "code": 200,
        "message": "success",
        "data": {
            "available": es_available,
            "index_name": INDEX_NAME,
            "storage_type": "elasticsearch" if es_available else "memory",
            "document_count": len(es_fallback_storage)
        }
    }


@router.on_event("startup")
async def startup_event():
    """启动时初始化 Elasticsearch"""
    init_elasticsearch()
    if es_available:
        create_index()
        print("[ES-Indexer] Elasticsearch 初始化完成")
    else:
        print("[ES-Indexer] Elasticsearch 不可用，使用内存降级方案")


@router.on_event("shutdown")
async def shutdown_event():
    """关闭时清理资源"""
    global es_client
    if es_client:
        es_client.close()
        print("[ES-Indexer] Elasticsearch 连接已关闭")
