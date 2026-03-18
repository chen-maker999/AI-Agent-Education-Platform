"""交叉编码器重排序 (CROSS-ENCODER)"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any
import numpy as np

router = APIRouter(prefix="/rerank", tags=["Cross-Encoder Reranker"])

cross_encoder_model = None
model_loaded = False


class RerankRequest(BaseModel):
    query: str
    documents: List[Dict[str, Any]]
    top_k: int = 5


class RerankRequestSimple(BaseModel):
    """简化版重排序请求"""
    query: str
    documents: List[Dict[str, Any]] = []
    top_k: int = 5


def load_model():
    global cross_encoder_model, model_loaded
    if model_loaded:
        return True
    try:
        from sentence_transformers import CrossEncoder
        cross_encoder_model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        model_loaded = True
        return True
    except:
        return False


async def rerank_documents(query: str, documents: List[Dict], top_k: int = 5) -> List[Dict]:
    load_model()
    
    if model_loaded and cross_encoder_model:
        doc_texts = [d.get("content", "") for d in documents]
        pairs = [(query, text) for text in doc_texts]
        scores = cross_encoder_model.predict(pairs)
        
        for i, doc in enumerate(documents):
            doc["rerank_score"] = float(scores[i])
    else:
        for doc in documents:
            doc["rerank_score"] = doc.get("score", 0.5)
    
    documents.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)
    return documents[:top_k]


@router.post("/rerank")
async def rerank_endpoint(request: RerankRequest):
    results = await rerank_documents(request.query, request.documents, request.top_k)
    return {"code": 200, "data": {"results": results, "total": len(results)}}


@router.post("/rerank/simple")
async def rerank_endpoint_simple(request: RerankRequestSimple):
    """简化版重排序"""
    docs = request.documents or [{"text": "document"}]
    results = await rerank_documents(request.query, docs, request.top_k)
    return {"code": 200, "data": {"results": results, "total": len(results)}}


@router.get("/status")
async def get_status():
    return {"code": 200, "data": {"model_loaded": model_loaded}}
