"""向量检索服务 - FAISS + PostgreSQL存储"""

import uuid
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import hashlib
import random

router = APIRouter(prefix="/knowledge/vector", tags=["Vector Search"])

# SQLAlchemy
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from common.database.postgresql import Base, AsyncSessionLocal
from common.core.config import settings


@router.get("/", response_model=dict)
async def get_vector_stats():
    """获取向量检索服务状态"""
    return {"code": 200, "message": "success", "data": {"status": "ok", "service": "vector search"}}


# 尝试导入FAISS
try:
    import faiss
    import numpy as np
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    np = None

# SQLAlchemy Model
class VectorDocument(Base):
    __tablename__ = "vector_documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doc_id = Column(String(100), unique=True, index=True)
    content = Column(Text, nullable=False)
    doc_metadata = Column(JSON)
    vector_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# FAISS索引管理
vector_index = None
doc_id_mapping: Dict[int, str] = {}
dimension = 768

class Document(BaseModel):
    content: str
    metadata: Dict[str, Any] = {}

class SearchQuery(BaseModel):
    query: str
    top_k: int = 5

class AddDocument(BaseModel):
    documents: List[Document]

def get_embedding(text: str) -> List[float]:
    if not FAISS_AVAILABLE or np is None:
        seed = sum(ord(c) for c in text)
        random.seed(seed)
        return [random.random() for _ in range(dimension)]
    np.random.seed(sum(ord(c) for c in text))
    return np.random.rand(dimension).tolist()

def init_faiss_index():
    global vector_index
    if FAISS_AVAILABLE and vector_index is None:
        vector_index = faiss.IndexFlatL2(dimension)

async def add_documents_to_index(documents: List[Document]):
    global vector_index, doc_id_mapping
    if not FAISS_AVAILABLE or np is None:
        return
    init_faiss_index()
    embeddings = [get_embedding(doc.content) for doc in documents]
    if embeddings:
        embeddings_array = np.array(embeddings).astype("float32")
        vector_index.add(embeddings_array)
        start_idx = vector_index.ntotal - len(embeddings)
        for i, doc in enumerate(documents):
            doc_id = hashlib.md5(doc.content.encode()).hexdigest()[:16]
            doc_id_mapping[start_idx + i] = doc_id

async def search_index(query: str, top_k: int = 5) -> List[Dict]:
    global vector_index, doc_id_mapping
    if not FAISS_AVAILABLE or np is None or vector_index is None or vector_index.ntotal == 0:
        return []
    query_embedding = np.array([get_embedding(query)]).astype("float32")
    search_k = min(top_k, vector_index.ntotal)
    distances, indices = vector_index.search(query_embedding, search_k)
    results = []
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        for i, idx in enumerate(indices[0]):
            if idx >= 0 and idx in doc_id_mapping:
                doc_id = doc_id_mapping[idx]
                result = await session.execute(select(VectorDocument).where(VectorDocument.doc_id == doc_id))
                doc = result.scalar_one_or_none()
                if doc:
                    results.append({"doc_id": doc.doc_id, "content": doc.content, "score": float(1/(1+distances[0][i])), "metadata": doc.doc_metadata or {}})
    return results

@router.post("/documents", status_code=201)
async def add_documents(data: AddDocument):
    global vector_index, doc_id_mapping
    init_faiss_index()
    doc_ids = []
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        for doc in data.documents:
            doc_id = hashlib.md5(doc.content.encode()).hexdigest()[:16]
            result = await session.execute(select(VectorDocument).where(VectorDocument.doc_id == doc_id))
            if result.scalar_one_or_none():
                continue
            vector_doc = VectorDocument(doc_id=doc_id, content=doc.content, doc_metadata=doc.metadata, vector_id=vector_index.ntotal if vector_index else None)
            session.add(vector_doc)
            doc_ids.append(doc_id)
        await session.commit()
    await add_documents_to_index(data.documents)
    return {"code": 201, "message": f"成功添加 {len(doc_ids)} 个文档", "data": {"doc_ids": doc_ids, "total": len(doc_ids), "indexed": FAISS_AVAILABLE}}

@router.post("/search")
async def search_documents(query: SearchQuery):
    if FAISS_AVAILABLE and vector_index is not None and vector_index.ntotal > 0:
        results = await search_index(query.query, query.top_k)
        if results:
            return {"code": 200, "message": "success", "data": {"query": query.query, "results": results, "total": len(results), "search_method": "faiss"}}
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        result = await session.execute(select(VectorDocument).where(VectorDocument.content.ilike(f"%{query.query}%")).limit(query.top_k))
        docs = result.scalars().all()
        results = [{"doc_id": doc.doc_id, "content": doc.content, "score": 0.8, "metadata": doc.doc_metadata or {}} for doc in docs]
    return {"code": 200, "message": "success", "data": {"query": query.query, "results": results, "total": len(results), "search_method": "keyword"}}

@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    async with AsyncSessionLocal() as session:
        from sqlalchemy import delete
        await session.execute(delete(VectorDocument).where(VectorDocument.doc_id == doc_id))
        await session.commit()
        return {"code": 200, "message": "文档删除成功"}

@router.get("/documents")
async def list_documents(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select, func
        count_result = await session.execute(select(func.count(VectorDocument.id)))
        total = count_result.scalar() or 0
        result = await session.execute(select(VectorDocument).order_by(VectorDocument.created_at.desc()).offset((page-1)*page_size).limit(page_size))
        docs = result.scalars().all()
        items = [{"doc_id": doc.doc_id, "content": doc.content[:200]+"..." if len(doc.content)>200 else doc.content, "metadata": doc.doc_metadata, "created_at": doc.created_at.isoformat() if doc.created_at else None} for doc in docs]
        return {"code": 200, "message": "success", "data": {"items": items, "total": total, "page": page, "page_size": page_size, "faiss_available": FAISS_AVAILABLE, "faiss_count": vector_index.ntotal if vector_index else 0}}

@router.get("/stats")
async def get_stats():
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select, func
        result = await session.execute(select(func.count(VectorDocument.id)))
        total_docs = result.scalar() or 0
    return {"code": 200, "message": "success", "data": {"total_documents": total_docs, "faiss_available": FAISS_AVAILABLE, "faiss_count": vector_index.ntotal if vector_index else 0, "dimension": dimension}}

@router.on_event("startup")
async def startup():
    init_faiss_index()
