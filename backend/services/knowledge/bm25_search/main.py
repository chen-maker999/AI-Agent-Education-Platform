"""BM25 关键词检索服务 - 基于 Elasticsearch 实现，支持内存降级"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import math
import hashlib
import json
import os
import pickle
from collections import defaultdict

try:
    from elasticsearch import Elasticsearch
    ELASTICSEARCH_AVAILABLE = True
except ImportError:
    ELASTICSEARCH_AVAILABLE = False

router = APIRouter(prefix="/bm25", tags=["BM25 Search"])


# ==================== 配置 ====================
# BM25 参数 - P11 优化：基于 F1 测试调整
BM25_K1 = 1.2  # P11 优化：从 1.5 降至 1.2，降低词频饱和度（测试显示 F1 更高）
BM25_B = 0.75  # 文档长度归一化参数

# Elasticsearch 配置
ES_HOST = os.getenv("ES_HOST", "localhost")
ES_PORT = int(os.getenv("ES_PORT", 9200))
ES_INDEX = os.getenv("ES_INDEX", "edu_bm25")
ES_USERNAME = os.getenv("ES_USERNAME", None)
ES_PASSWORD = os.getenv("ES_PASSWORD", None)

# 索引映射配置
ES_INDEX_MAPPING = {
    "mappings": {
        "properties": {
            "doc_id": {"type": "keyword"},
            "content": {"type": "text", "analyzer": "standard"},
            "course_id": {"type": "keyword"},
            "metadata": {"type": "object"},
            "content_tokens": {"type": "text", "analyzer": "standard"},
            "created_at": {"type": "date"},
            "updated_at": {"type": "date"}
        }
    },
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "similarity": {
            "custom_bm25": {
                "type": "BM25",
                "b": BM25_B,
                "k1": BM25_K1
            }
        }
    }
}


# ==================== 数据模型 ====================
class BM25Document(BaseModel):
    """BM25 文档"""
    doc_id: str
    content: str
    metadata: Dict[str, Any] = {}
    course_id: Optional[str] = None


class BM25IndexRequest(BaseModel):
    """索引请求"""
    documents: List[BM25Document]


class BM25SearchRequest(BaseModel):
    """搜索请求"""
    query: str
    course_id: Optional[str] = None
    top_k: int = 10


class BM25SearchResponse(BaseModel):
    """搜索响应"""
    query: str
    results: List[Dict[str, Any]]
    total: int
    search_time: float


# ==================== Elasticsearch 客户端 ====================
class ESClient:
    """Elasticsearch 客户端封装"""

    def __init__(self):
        self.client: Optional[Elasticsearch] = None
        self.available = False

    def connect(self) -> bool:
        """连接 Elasticsearch"""
        if not ELASTICSEARCH_AVAILABLE:
            print("[BM25] Elasticsearch 客户端未安装")
            return False

        try:
            es_url = f"http://{ES_HOST}:{ES_PORT}"
            if ES_USERNAME and ES_PASSWORD:
                es_url = f"http://{ES_USERNAME}:{ES_PASSWORD}@{ES_HOST}:{ES_PORT}"

            self.client = Elasticsearch(
                [es_url],
                request_timeout=30,
                max_retries=3,
                retry_on_timeout=True
            )

            if self.client.ping():
                self.available = True
                print("[BM25] Elasticsearch 连接成功")
                return True
            else:
                print("[BM25] Elasticsearch 连接失败")
                return False
        except Exception as e:
            print(f"[BM25] Elasticsearch 初始化失败：{e}")
            return False

    def create_index(self) -> bool:
        """创建索引"""
        if not self.available:
            return False

        try:
            if not self.client.indices.exists(index=ES_INDEX):
                self.client.indices.create(index=ES_INDEX, body=ES_INDEX_MAPPING)
                print(f"[BM25] 索引 {ES_INDEX} 创建成功")
            return True
        except Exception as e:
            print(f"[BM25] 创建索引失败：{e}")
            return False

    def index_documents(self, documents: List[BM25Document]) -> int:
        """索引文档"""
        if not self.available:
            return 0

        try:
            bulk_data = []
            for doc in documents:
                bulk_data.append({"index": {"_index": ES_INDEX, "_id": doc.doc_id}})
                bulk_data.append({
                    "doc_id": doc.doc_id,
                    "content": doc.content,
                    "course_id": doc.course_id,
                    "metadata": doc.metadata,
                    "content_tokens": doc.content,
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                })

            if bulk_data:
                response = self.client.bulk(body=bulk_data, refresh=True)
                return len(documents)
        except Exception as e:
            print(f"[BM25] ES 批量索引失败：{e}")

        return 0

    def search(self, query: str, course_id: Optional[str] = None, top_k: int = 10) -> List[Dict]:
        """搜索文档"""
        if not self.available:
            return []

        try:
            must = [{"match": {"content_tokens": query}}]
            if course_id:
                must.append({"term": {"course_id": course_id}})

            query_body = {
                "query": {"bool": {"must": must}},
                "size": top_k,
                "highlight": {
                    "fields": {
                        "content": {"fragment_size": 150, "number_of_fragments": 3}
                    }
                }
            }

            response = self.client.search(index=ES_INDEX, body=query_body)
            results = []
            for hit in response["hits"]["hits"]:
                source = hit["_source"]
                results.append({
                    "doc_id": source.get("doc_id"),
                    "content": source.get("content", ""),
                    "score": hit["_score"],
                    "highlights": hit.get("highlight", {}),
                    "course_id": source.get("course_id"),
                    "metadata": source.get("metadata", {})
                })
            return results
        except Exception as e:
            print(f"[BM25] ES 搜索失败：{e}")
            return []

    def delete_document(self, doc_id: str) -> bool:
        """删除文档"""
        if not self.available:
            return False

        try:
            self.client.delete(index=ES_INDEX, id=doc_id, ignore=[404])
            return True
        except Exception as e:
            print(f"[BM25] ES 删除失败：{e}")
            return False

    def get_stats(self) -> Dict:
        """获取统计信息"""
        if not self.available:
            return {"available": False}

        try:
            count = self.client.count(index=ES_INDEX)
            return {
                "available": True,
                "index_name": ES_INDEX,
                "document_count": count["count"],
                "storage_type": "elasticsearch"
            }
        except Exception as e:
            print(f"[BM25] ES 获取统计失败：{e}")
            return {"available": False}

    def close(self):
        """关闭连接"""
        if self.client:
            self.client.close()


# ==================== 内存 BM25 索引 (降级方案) ====================
class BM25Index:
    """BM25 索引实现 - 内存降级方案"""

    def __init__(self):
        self.documents: Dict[str, BM25Document] = {}
        self.doc_lengths: Dict[str, int] = {}
        self.avg_doc_length: float = 0.0
        self.inverted_index: Dict[str, Dict[str, int]] = defaultdict(dict)
        self.doc_frequency: Dict[str, int] = defaultdict(int)
        self.total_docs: int = 0
        self.vocabulary: set = set()

    def tokenize(self, text: str) -> List[str]:
        """中文分词"""
        try:
            import jieba
            words = jieba.cut(text)
            stopwords = {
                '的', '是', '在', '和', '了', '有', '我', '你', '他', '她', '它', '们',
                '这', '那', '个', '与', '或', '及', '等', '为', '以', '于', '也', '就',
                '都', '而', '着', '一个', '没有', '我们', '你们', '可以', '进行', '使用',
                '来', '去', '很', '更', '最', '把', '被', '让', '叫', '使', '令'
            }
            tokens = [w for w in words if w.strip() and len(w) > 1 and w not in stopwords]
            return tokens
        except ImportError:
            import re
            tokens = re.findall(r'[\u4e00-\u9fa5]{2,}|[a-zA-Z]{3,}', text)
            return tokens

    def add_document(self, doc: BM25Document):
        """添加文档到索引"""
        doc_id = doc.doc_id
        if doc_id in self.documents:
            self.remove_document(doc_id)

        tokens = self.tokenize(doc.content)
        self.documents[doc_id] = doc
        self.doc_lengths[doc_id] = len(tokens)
        self.total_docs = len(self.documents)

        total_length = sum(self.doc_lengths.values())
        self.avg_doc_length = total_length / self.total_docs if self.total_docs > 0 else 0

        term_freq = defaultdict(int)
        for token in tokens:
            term_freq[token] += 1
            self.vocabulary.add(token)

        for term, freq in term_freq.items():
            if doc_id not in self.inverted_index[term]:
                self.doc_frequency[term] += 1
            self.inverted_index[term][doc_id] = freq

    def remove_document(self, doc_id: str):
        """从索引删除文档"""
        if doc_id not in self.documents:
            return

        old_doc = self.documents[doc_id]
        tokens = self.tokenize(old_doc.content)

        for token in set(tokens):
            if token in self.inverted_index and doc_id in self.inverted_index[token]:
                del self.inverted_index[token][doc_id]
                self.doc_frequency[token] -= 1
                if self.doc_frequency[token] <= 0:
                    del self.doc_frequency[token]
                    self.vocabulary.discard(token)

        del self.documents[doc_id]
        del self.doc_lengths[doc_id]
        self.total_docs = len(self.documents)

        if self.total_docs > 0:
            total_length = sum(self.doc_lengths.values())
            self.avg_doc_length = total_length / self.total_docs

    def bm25_score(self, term: str, doc_id: str) -> float:
        """计算单个词的 BM25 分数"""
        if term not in self.vocabulary or doc_id not in self.documents:
            return 0.0

        tf = self.inverted_index[term].get(doc_id, 0)
        if tf == 0:
            return 0.0

        df = self.doc_frequency.get(term, 0)
        if df == 0:
            return 0.0

        doc_len = self.doc_lengths[doc_id]

        idf = math.log((self.total_docs - df + 0.5) / (df + 0.5) + 1.0)
        tf_norm = (tf * (BM25_K1 + 1)) / (tf + BM25_K1 * (1 - BM25_B + BM25_B * doc_len / self.avg_doc_length))

        return idf * tf_norm

    def search(self, query: str, course_id: Optional[str] = None, top_k: int = 15, use_query_rewrite: bool = True) -> List[Dict]:
        """
        BM25 搜索

        Args:
            query: 查询文本
            course_id: 课程 ID 过滤（可选）
            top_k: 返回结果数量（P11 优化：从 10 提升至 15，增加召回率）
            use_query_rewrite: 是否使用查询改写（中文->英文）
        """
        # 查询改写：中文 -> 英文
        if use_query_rewrite:
            try:
                from services.knowledge.query_rewriter import rewrite_query
                expanded_query = rewrite_query(query)
                query = expanded_query
            except Exception as e:
                print(f"[BM25] 查询改写失败：{e}")
        
        tokens = self.tokenize(query)
        if not tokens:
            return []

        doc_scores: Dict[str, float] = defaultdict(float)

        for token in tokens:
            if token not in self.vocabulary:
                continue
            for doc_id in self.inverted_index[token]:
                if course_id and self.documents[doc_id].course_id != course_id:
                    continue
                score = self.bm25_score(token, doc_id)
                doc_scores[doc_id] += score

        # 应用文档质量过滤和重排序
        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)

        results = []
        for doc_id, score in sorted_docs[:top_k * 2]:  # 先取更多结果用于质量过滤
            if score > 0:
                doc = self.documents[doc_id]
                results.append({
                    "doc_id": doc.doc_id,
                    "content": doc.content[:500],
                    "score": round(score, 4),
                    "metadata": doc.metadata or {},
                    "course_id": doc.course_id
                })
        
        # 应用质量过滤
        if results:
            try:
                from services.knowledge.document_filter import DocumentQualityFilter
                quality_filter = DocumentQualityFilter()
                
                # 过滤低质量文档
                filtered_results = quality_filter.filter_documents(results)
                
                # 如果过滤后结果太少，放宽限制
                if len(filtered_results) < min(5, top_k):
                    filtered_results = results[:top_k]
                else:
                    # 按质量分数重排序
                    scored = quality_filter.rank_documents(filtered_results)
                    filtered_results = [doc for doc, _ in scored[:top_k]]
                
                results = filtered_results
            except Exception as e:
                print(f"[BM25] 质量过滤失败：{e}")
                results = results[:top_k]

        return results

    def get_stats(self) -> Dict:
        """获取索引统计"""
        return {
            "total_docs": self.total_docs,
            "vocabulary_size": len(self.vocabulary),
            "avg_doc_length": round(self.avg_doc_length, 2),
            "index_size": sum(len(docs) for docs in self.inverted_index.values()),
            "storage_type": "memory"
        }

    def save(self, path: str = "data/bm25_index.pkl"):
        """保存索引到磁盘"""
        import pickle
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # 转换为可序列化的格式
        data = {
            "documents": {k: v.dict() if hasattr(v, 'dict') else v for k, v in self.documents.items()},
            "doc_lengths": dict(self.doc_lengths),
            "avg_doc_length": self.avg_doc_length,
            "inverted_index": {k: dict(v) for k, v in self.inverted_index.items()},
            "doc_frequency": dict(self.doc_frequency),
            "total_docs": self.total_docs,
            "vocabulary": list(self.vocabulary) if isinstance(self.vocabulary, set) else self.vocabulary,
            "version": "1.0"
        }
        with open(path, 'wb') as f:
            pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
        print(f"[BM25] 索引已保存：{path} ({self.total_docs} 个文档)")

    def load(self, path: str = "data/bm25_index.pkl") -> bool:
        """从磁盘加载索引"""
        import pickle
        if not os.path.exists(path):
            print(f"[BM25] 索引文件不存在：{path}")
            return False
        try:
            with open(path, 'rb') as f:
                data = pickle.load(f)
            
            # 验证数据有效性
            if not data or data.get("total_docs", 0) == 0:
                print(f"[BM25] 索引文件为空或无效：{path}")
                return False
            
            # 恢复为正确的数据类型
            self.documents = {}
            for doc_id, doc_data in data.get("documents", {}).items():
                if isinstance(doc_data, dict):
                    self.documents[doc_id] = BM25Document(**doc_data)
                else:
                    self.documents[doc_id] = doc_data
            
            self.doc_lengths = dict(data.get("doc_lengths", {}))
            self.avg_doc_length = data.get("avg_doc_length", 0.0)
            
            # 恢复 defaultdict
            self.inverted_index = defaultdict(dict)
            for term, docs in data.get("inverted_index", {}).items():
                self.inverted_index[term] = dict(docs)
            
            self.doc_frequency = defaultdict(int, data.get("doc_frequency", {}))
            self.total_docs = data.get("total_docs", 0)
            
            # 恢复 set
            vocab = data.get("vocabulary", [])
            self.vocabulary = set(vocab) if isinstance(vocab, list) else vocab
            
            print(f"[BM25] 索引已加载：{path} ({self.total_docs} 个文档)")
            return True
        except Exception as e:
            print(f"[BM25] 索引加载失败：{e}")
            import traceback
            traceback.print_exc()
            return False


# ==================== 全局实例 ====================
es_client = ESClient()
bm25_index = BM25Index()
_index_loaded = False  # 标记索引是否已成功加载


@router.on_event("startup")
async def startup_event():
    """启动时初始化"""
    global _index_loaded
    
    # 尝试连接 ES
    es_connected = es_client.connect()
    if es_connected:
        es_client.create_index()
        _index_loaded = True
    else:
        # ES 不可用，加载内存索引
        _index_loaded = bm25_index.load()
        if _index_loaded:
            print("[BM25] 使用内存 BM25 索引（从磁盘加载）")
        else:
            print("[BM25] 使用内存 BM25 索引（降级方案，索引为空）")


@router.on_event("shutdown")
async def shutdown_event():
    """关闭时清理资源"""
    if es_client.available:
        es_client.close()
    else:
        # 只在索引已加载且有数据时才保存
        if _index_loaded and bm25_index.total_docs > 0:
            bm25_index.save()
        else:
            print(f"[BM25] 跳过保存：索引未加载或为空 (total_docs={bm25_index.total_docs})")
    print("[BM25] 服务已关闭")


# ==================== API 接口 ====================
@router.post("/index", status_code=201)
async def index_documents(request: BM25IndexRequest):
    """索引文档"""
    start_time = datetime.now()

    if es_client.available:
        # 使用 ES 索引
        indexed_count = es_client.index_documents(request.documents)
        storage_type = "elasticsearch"
    else:
        # 使用内存索引
        for doc in request.documents:
            bm25_index.add_document(doc)
        indexed_count = len(request.documents)
        storage_type = "memory"
        bm25_index.save()

    processing_time = (datetime.now() - start_time).total_seconds()

    return {
        "code": 201,
        "message": f"成功索引 {indexed_count} 个文档",
        "data": {
            "indexed_count": indexed_count,
            "total_docs": indexed_count,
            "storage_type": storage_type,
            "processing_time": round(processing_time, 3)
        }
    }


@router.post("/search")
async def search_documents(request: BM25SearchRequest):
    """BM25 搜索"""
    start_time = datetime.now()

    if es_client.available:
        # 使用 ES 搜索
        results = es_client.search(
            query=request.query,
            course_id=request.course_id,
            top_k=request.top_k
        )
    else:
        # 使用内存搜索
        results = bm25_index.search(
            query=request.query,
            course_id=request.course_id,
            top_k=request.top_k
        )

    search_time = (datetime.now() - start_time).total_seconds()

    return BM25SearchResponse(
        query=request.query,
        results=results,
        total=len(results),
        search_time=round(search_time, 3)
    )


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """删除文档"""
    if es_client.available:
        success = es_client.delete_document(doc_id)
    else:
        bm25_index.remove_document(doc_id)
        bm25_index.save()
        success = True

    return {
        "code": 200,
        "message": "文档删除成功" if success else "删除失败"
    }


@router.get("/stats")
async def get_stats():
    """获取索引统计"""
    if es_client.available:
        stats = es_client.get_stats()
    else:
        stats = bm25_index.get_stats()

    return {
        "code": 200,
        "message": "success",
        "data": {
            **stats,
            "k1": BM25_K1,
            "b": BM25_B
        }
    }


@router.post("/clear")
async def clear_index():
    """清空索引"""
    global bm25_index
    if es_client.available:
        if es_client.client:
            es_client.client.indices.delete(index=ES_INDEX, ignore=[400, 404])
            es_client.create_index()
    else:
        bm25_index = BM25Index()

    return {"code": 200, "message": "索引已清空"}


@router.post("/reset-params")
async def reset_params(k1: float = 1.5, b: float = 0.75):
    """重置 BM25 参数"""
    global BM25_K1, BM25_B
    BM25_K1 = k1
    BM25_B = b

    return {
        "code": 200,
        "message": "参数已更新",
        "data": {"k1": BM25_K1, "b": BM25_B}
    }


@router.get("/config")
async def get_config():
    """获取当前配置"""
    return {
        "code": 200,
        "data": {
            "k1": BM25_K1,
            "b": BM25_B,
            "es_available": es_client.available,
            "description": {
                "k1": "词频饱和度参数 (1.2-2.0, 越大词频影响越大)",
                "b": "文档长度归一化参数 (0-1, 越大长度影响越大)"
            }
        }
    }
