"""RAG主服务 - PostgreSQL存储"""

import uuid
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import os
import hashlib

router = APIRouter(prefix="/knowledge/rag", tags=["RAG Service"])

# SQLAlchemy
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from common.database.postgresql import Base, AsyncSessionLocal
from common.core.config import settings

# SQLAlchemy Model
class RAGDocument(Base):
    __tablename__ = "rag_documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doc_id = Column(String(100), unique=True, index=True)
    content = Column(Text, nullable=False)
    doc_metadata = Column("doc_metadata", JSON)
    course_id = Column(String(100), index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RAGSession(Base):
    __tablename__ = "rag_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(100), unique=True, index=True)
    student_id = Column(String(100), index=True)
    query = Column(Text)
    answer = Column(Text)
    sources = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)


class RAGRequest(BaseModel):
    query: str
    student_id: str
    course_id: Optional[str] = None
    session_id: Optional[str] = None
    use_rewrite: bool = True
    use_rerank: bool = True
    channels: List[str] = ["semantic", "keyword", "graph"]
    top_k: int = 10


class RAGRequestSimple(BaseModel):
    """简化版RAG请求"""
    session_id: Optional[str] = None
    student_id: str
    message: str = ""


class RAGResponse(BaseModel):
    answer: str
    sources: List[Dict]
    session_id: str
    intent: str
    processing_time: float


async def search_local_documents(query: str, course_id: str = "default", top_k: int = 10) -> List[Dict]:
    """从数据库中检索"""
    from services.knowledge.vector.main import search_documents, SearchQuery

    try:
        search_req = SearchQuery(query=query, top_k=top_k, use_hybrid=False)
        results = await search_documents(search_req)
        return results.get("data", {}).get("results", []) if isinstance(results, dict) else []
    except Exception as e:
        print(f"向量检索失败: {e}")
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(RAGDocument).where(
                    RAGDocument.content.ilike(f"%{query}%"),
                    RAGDocument.course_id == course_id
                ).limit(top_k)
            )
            docs = result.scalars().all()
            return [{"doc_id": doc.doc_id, "content": doc.content, "doc_metadata": doc.doc_metadata or {}, "score": 0.8} for doc in docs]


async def process_rag_request(request: RAGRequest) -> Dict:
    """完整的RAG处理流程"""
    start_time = datetime.now()

    # 0. 优先从本地文档存储检索
    local_results = await search_local_documents(request.query, request.course_id or "default", request.top_k)

    # 1. 查询改写
    expanded_queries = [request.query]
    if request.use_rewrite:
        try:
            from services.knowledge.query_rewrite.main import rewrite_query
            expanded_queries = await rewrite_query(request.query, request.course_id or "")
        except:
            pass

    # 2. 意图识别
    intent = "general"
    try:
        from services.knowledge.router.main import classify_intent
        intent, _, request.channels = classify_intent(request.query)
    except:
        pass

    # 3. 多路检索（作为补充）
    all_results = local_results.copy()

    if not local_results:
        for query in expanded_queries:
            try:
                from services.knowledge.search.main import multi_channel_search
                results = await multi_channel_search(query, request.channels, request.course_id, request.top_k)
                for channel, docs in results.items():
                    all_results.extend(docs)
            except Exception as e:
                print(f"检索错误: {e}")
    
    # 4. 结果融合
    try:
        from services.knowledge.fusion.main import fuse_results, FusionRequest
        fusion_req = FusionRequest(
            channel_results={"merged": all_results},
            top_k=request.top_k
        )
        fused_results = fuse_results(fusion_req)
    except:
        fused_results = all_results[:request.top_k]
    
    # 5. 重排序
    if request.use_rerank and fused_results:
        try:
            from services.knowledge.rerank.main import rerank_documents
            fused_results = await rerank_documents(request.query, fused_results, request.top_k)
        except:
            pass
    
    # 6. 上下文修剪
    try:
        from services.knowledge.trimmer.main import trim_context, TrimRequest
        trimmed_docs = trim_context(TrimRequest(documents=fused_results, max_tokens=3000))
    except:
        trimmed_docs = fused_results[:5]
    
    # 7. 生成回答
    answer = ""
    try:
        from common.integration.kimi import get_kimi_response
        
        context_text = "\n\n".join([
            f"参考{i+1}: {d.get('content', '')[:500]}"
            for i, d in enumerate(trimmed_docs[:3])
        ])
        
        prompt = f"""你是一个智能教学助手。根据以下参考知识回答学生问题。

参考知识：
{context_text}

学生问题：{request.query}

要求：用中文回答，简洁准确。"""
        
        answer = await get_kimi_response(
            prompt=prompt,
            system_prompt="你是一位专业的编程教师，擅长用简洁易懂的语言解释编程概念。"
        )
    except Exception as e:
        answer = f"根据检索到的资料：{trimmed_docs[0].get('content', '')[:200]}..." if trimmed_docs else "抱歉，无法生成回答"
    
    processing_time = (datetime.now() - start_time).total_seconds()

    # 8. 保存会话到数据库
    session_id = request.session_id or str(uuid.uuid4())
    async with AsyncSessionLocal() as session:
        rag_session = RAGSession(
            session_id=session_id,
            student_id=request.student_id,
            query=request.query,
            answer=answer,
            sources=trimmed_docs
        )
        session.add(rag_session)
        await session.commit()
    
    return {
        "answer": answer,
        "sources": trimmed_docs,
        "intent": intent,
        "processing_time": processing_time,
        "session_id": session_id
    }


@router.post("/chat", response_model=RAGResponse)
async def rag_chat(request: RAGRequest):
    """RAG对话接口"""
    session_id = request.session_id or str(uuid.uuid4())
    
    result = await process_rag_request(request)
    
    return RAGResponse(
        answer=result["answer"],
        sources=result["sources"],
        session_id=session_id,
        intent=result["intent"],
        processing_time=result["processing_time"]
    )


@router.post("/chat/simple")
async def rag_chat_simple(request: RAGRequestSimple):
    """简化版RAG对话"""
    session_id = request.session_id or str(uuid.uuid4())
    
    simple_request = RAGRequest(
        query=request.message or "你好",
        student_id=request.student_id,
        session_id=session_id,
        use_rewrite=False,
        use_rerank=False,
        top_k=3
    )
    
    result = await process_rag_request(simple_request)
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "answer": result["answer"],
            "session_id": session_id,
            "sources": result["sources"]
        }
    }


async def process_file_upload(file_content: bytes, filename: str, course_id: str = "default") -> Dict:
    """处理文件上传：读取内容、分块、向量化、存储"""
    from services.knowledge.chunk.main import chunk_text, ChunkRequest
    from services.knowledge.vector.main import add_documents, Document
    import io

    # 1. 读取文件内容
    ext = filename.split('.')[-1].lower() if '.' in filename else ''
    
    if ext == 'pdf':
        # PDF 文件需要特殊处理
        try:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(file_content)) as pdf:
                text_parts = []
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
            content = '\n\n'.join(text_parts)
            if not content.strip():
                raise ValueError("PDF 文本提取失败")
        except Exception as e:
            raise ValueError(f"PDF 解析失败: {str(e)},请确保 PDF 包含可提取的文本")
    else:
        # 普通文本文件
        try:
            content = file_content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                content = file_content.decode('gbk')
            except:
                content = file_content.decode('utf-8', errors='ignore')

    # 2. 智能分块
    chunk_req = ChunkRequest(content=content, content_type="教材", doc_metadata={"filename": filename})
    chunk_response = await chunk_text(chunk_req)
    chunks = chunk_response.chunks

    # 3. 存储文档并建立索引
    doc_ids = []
    docs_to_index = []

    for i, chunk in enumerate(chunks):
        doc_id = hashlib.md5(f"{filename}_{i}_{course_id}".encode()).hexdigest()
        doc_ids.append(doc_id)

        doc = Document(
            content=chunk["content"],
            metadata={
                "filename": filename,
                "chunk_index": i,
                "course_id": course_id,
                "doc_id": doc_id
            }
        )
        docs_to_index.append(doc)

        # 存储到PostgreSQL
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select
            existing = await session.execute(
                select(RAGDocument).where(RAGDocument.doc_id == doc_id)
            )
            if not existing.scalar_one_or_none():
                rag_doc = RAGDocument(
                    doc_id=doc_id,
                    content=chunk["content"],
                    doc_metadata=doc.metadata,
                    course_id=course_id
                )
                session.add(rag_doc)
                await session.commit()

    # 4. 添加到向量索引
    try:
        from services.knowledge.vector.main import add_documents as vector_add_documents
        from services.knowledge.vector.main import AddDocument as VectorAddDocument
        await vector_add_documents(VectorAddDocument(documents=docs_to_index))
    except Exception as e:
        print(f"向量索引添加失败: {e}")

    return {
        "doc_ids": doc_ids,
        "total_chunks": len(doc_ids),
        "filename": filename
    }


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    course_id: str = Form("default")
):
    """上传文档到知识库"""
    try:
        file_content = await file.read()
        result = await process_file_upload(file_content, file.filename, course_id)

        return {
            "code": 200,
            "message": "文档上传成功",
            "data": {
                "filename": result["filename"],
                "doc_count": result["total_chunks"],
                "doc_ids": result["doc_ids"]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件处理失败: {str(e)}")


@router.get("/documents")
async def list_documents(
    course_id: str = "default",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """列出已上传的文档"""
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select, func
        
        count_result = await session.execute(
            select(func.count(RAGDocument.id)).where(RAGDocument.course_id == course_id)
        )
        total = count_result.scalar() or 0
        
        result = await session.execute(
            select(RAGDocument)
            .where(RAGDocument.course_id == course_id)
            .order_by(RAGDocument.created_at.desc())
            .offset((page-1)*page_size)
            .limit(page_size)
        )
        docs = result.scalars().all()
        
        items = [{
            "doc_id": doc.doc_id,
            "content": doc.content[:200] + "..." if len(doc.content) > 200 else doc.content,
            "doc_metadata": doc.doc_metadata,
            "created_at": doc.created_at.isoformat() if doc.created_at else None
        } for doc in docs]

    return {
        "code": 200,
        "message": "success",
        "data": {"items": items, "total": total, "page": page, "page_size": page_size}
    }


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """删除文档"""
    async with AsyncSessionLocal() as session:
        from sqlalchemy import delete
        await session.execute(delete(RAGDocument).where(RAGDocument.doc_id == doc_id))
        await session.commit()
        return {"code": 200, "message": "删除成功"}


@router.get("/history/{student_id}")
async def get_chat_history(
    student_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """获取学生的对话历史"""
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select, func
        
        count_result = await session.execute(
            select(func.count(RAGSession.id)).where(RAGSession.student_id == student_id)
        )
        total = count_result.scalar() or 0
        
        result = await session.execute(
            select(RAGSession)
            .where(RAGSession.student_id == student_id)
            .order_by(RAGSession.created_at.desc())
            .offset((page-1)*page_size)
            .limit(page_size)
        )
        sessions = result.scalars().all()
        
        items = [{
            "session_id": s.session_id,
            "query": s.query,
            "answer": s.answer,
            "sources": s.sources,
            "created_at": s.created_at.isoformat() if s.created_at else None
        } for s in sessions]

    return {
        "code": 200,
        "message": "success",
        "data": {"items": items, "total": total}
    }


@router.get("/health")
async def rag_health():
    """RAG服务健康检查"""
    return {
        "code": 200,
        "message": "RAG服务运行中",
        "data": {
            "components": [
                "chunk_engine",
                "embedding_service",
                "faiss_indexer",
                "query_rewrite",
                "router",
                "search",
                "fusion",
                "rerank",
                "trimmer"
            ]
        }
    }
