"""上下文修剪 (CONTEXT-TRIMMER) - Token预算优化"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any

router = APIRouter(prefix="/context", tags=["Context Trimmer"])

MAX_TOKENS = 3000


class TrimRequest(BaseModel):
    documents: List[Dict[str, Any]]
    max_tokens: int = MAX_TOKENS
    mmr_lambda: float = 0.5


def estimate_tokens(text: str) -> int:
    chinese = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
    english = len([c for c in text if c.isascii()])
    return int(chinese / 1.5 + english / 4)


def trim_context(request: TrimRequest) -> List[Dict]:
    if not request.documents:
        return []
    
    docs = sorted(request.documents, key=lambda x: x.get("rerank_score", x.get("score", 0)), reverse=True)
    
    trimmed = []
    total_tokens = 0
    
    for doc in docs:
        doc_tokens = estimate_tokens(doc.get("content", ""))
        
        if total_tokens + doc_tokens <= request.max_tokens:
            trimmed.append(doc)
            total_tokens += doc_tokens
        elif len(trimmed) == 0:
            content = doc.get("content", "")
            trimmed_content = content[:request.max_tokens * 2]
            doc["content"] = trimmed_content
            trimmed.append(doc)
            break
    
    return trimmed


@router.post("/trim")
async def trim_context_endpoint(request: TrimRequest):
    trimmed = trim_context(request)
    return {"code": 200, "data": {"documents": trimmed, "count": len(trimmed)}}
