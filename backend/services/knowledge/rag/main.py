"""RAG主服务 - 简化版：TF-IDF + BM25 混合检索"""

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
    use_rerank: bool = False
    semantic_weight: float = 0.5
    keyword_weight: float = 0.5
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


async def process_rag_request(request: RAGRequest) -> Dict:
    """完整的RAG处理流程 - 简化版"""
    start_time = datetime.now()

    # 1. 查询改写
    expanded_queries = [request.query]
    if request.use_rewrite:
        try:
            from services.knowledge.query.main import rewrite_query
            expanded_queries = rewrite_query(request.query, request.course_id or "")
        except Exception as e:
            print(f"查询改写失败: {e}")

    # 2. 检索文档
    all_results = []

    # 检索所有文档
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        result = await session.execute(select(RAGDocument).limit(10))
        docs = result.scalars().all()

    import sys
    print(f"检索到 {len(docs)} 个文档", flush=True)
    sys.stdout.flush()

    if docs:
        # 直接返回前5个文档作为结果
        for doc in docs[:5]:
            all_results.append({
                "doc_id": doc.doc_id,
                "content": doc.content,
                "score": 1.0,
                "doc_metadata": doc.doc_metadata
            })
        print(f"返回 {len(all_results)} 个结果", flush=True)
    else:
        # 如果没有文档，返回测试消息
        print("警告: 数据库中没有文档！", flush=True)

    # 3. 如果没有结果，使用扩展查询重试
    if not all_results and len(expanded_queries) > 1:
        for eq in expanded_queries[1:]:
            async with AsyncSessionLocal() as session:
                from sqlalchemy import select
                # 只在有 course_id 时才过滤
                if request.course_id:
                    result = await session.execute(
                        select(RAGDocument).where(
                            RAGDocument.content.ilike(f"%{eq}%"),
                            RAGDocument.course_id == request.course_id
                        ).limit(request.top_k)
                    )
                else:
                    result = await session.execute(
                        select(RAGDocument).where(
                            RAGDocument.content.ilike(f"%{eq}%")
                        ).limit(request.top_k)
                    )
                docs = result.scalars().all()
            
            for doc in docs:
                all_results.append({
                    "doc_id": doc.doc_id,
                    "content": doc.content,
                    "score": 0.6,
                    "doc_metadata": doc.doc_metadata
                })
            
            if all_results:
                break

    # 4. 截取上下文
    trimmed_docs = []
    total_length = 0
    max_length = 3000
    
    for doc in all_results:
        content = doc.get('content', '')
        if total_length + len(content) <= max_length:
            trimmed_docs.append(doc)
            total_length += len(content)
        elif len(content) <= max_length:
            trimmed_docs.append(doc)
            total_length += len(content)
            if total_length >= max_length:
                break
    
    if not trimmed_docs:
        trimmed_docs = all_results[:5]

    # 5. 生成回答
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
        print(f"生成回答失败: {e}")
        answer = f"根据检索到的资料：{trimmed_docs[0].get('content', '')[:200]}..." if trimmed_docs else "抱歉，无法生成回答"
    
    processing_time = (datetime.now() - start_time).total_seconds()

    # 6. 保存会话到数据库 (每次都生成新的session_id以避免唯一约束冲突)
    new_session_id = str(uuid.uuid4())
    async with AsyncSessionLocal() as session:
        rag_session = RAGSession(
            session_id=new_session_id,
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
        "intent": "general",
        "processing_time": processing_time,
        "session_id": new_session_id
    }


@router.post("/chat")
async def rag_chat(request: RAGRequest):
    """RAG对话接口"""
    session_id = request.session_id or str(uuid.uuid4())

    try:
        result = await process_rag_request(request)

        # 返回统一格式
        return {
            "code": 200,
            "message": "success",
            "data": {
                "answer": result["answer"],
                "sources": result["sources"],
                "session_id": session_id,
                "intent": result["intent"],
                "processing_time": result["processing_time"]
            }
        }
    except Exception as e:
        print(f"RAG聊天错误: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"RAG处理失败: {str(e)}")


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
    print(f"[DEBUG upload] course_id={course_id}, filename={filename}", flush=True)
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

    # 4. 添加到向量索引和BM25索引
    try:
        from services.knowledge.vector.main import add_documents as vector_add_documents
        from services.knowledge.vector.main import AddDocument as VectorAddDocument
        await vector_add_documents(VectorAddDocument(documents=docs_to_index))
    except Exception as e:
        print(f"向量索引添加失败: {e}")
    
    # 5. 更新TF-IDF索引
    try:
        from services.knowledge.embedding.tfidf_main import add_documents_tfidf
        contents = [chunk["content"] for chunk in chunks]
        await add_documents_tfidf(doc_ids, contents)
    except Exception as e:
        print(f"TF-IDF索引更新失败: {e}")

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
    page_size: int = Query(20, ge=1, le=500),
    all_courses: bool = Query(False, description="为 true 时列出所有 course_id 下的文档（按 知识库+文件名 分组）"),
):
    """列出已上传的文档（按文件名去重聚合块数）。all_courses=true 时不过滤 course_id，用于知识库页展示 Agent/脚本导入的文档。"""
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select, func, cast, String, text

        # 使用 text() 函数直接执行 JSON 操作
        # PostgreSQL JSON -> text 需要使用 ::text 或 ->> 运算符

        if all_courses:
            # 全局：按 (course_id, filename) 分组
            # 直接查询所有文档，然后按文件名分组
            result = await session.execute(
                select(
                    RAGDocument.course_id,
                    RAGDocument.doc_metadata,
                    func.count(RAGDocument.id).label("doc_count"),
                )
                .group_by(RAGDocument.course_id, RAGDocument.doc_metadata)
                .order_by(RAGDocument.course_id)
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            rows = result.all()

            # 按文件名聚合
            file_map = {}
            for row in rows:
                cid = row.course_id or ""
                fname = None
                if row.doc_metadata and isinstance(row.doc_metadata, dict):
                    fname = row.doc_metadata.get('filename')
                if fname:
                    key = (cid, fname)
                    if key in file_map:
                        file_map[key] += row.doc_count
                    else:
                        file_map[key] = row.doc_count

            # 获取总数
            count_result = await session.execute(
                select(func.count(RAGDocument.id))
            )
            total = count_result.scalar() or 0

            items = []
            for (cid, fname), doc_count in file_map.items():
                items.append({
                    "doc_id": f"file_{cid}_{fname}",
                    "filename": fname,
                    "course_id": cid,
                    "doc_count": doc_count,
                    "doc_metadata": {"filename": fname, "course_id": cid},
                })

            # 如果没有数据，返回空列表
            if not items:
                items = []
        else:
            # 只查询指定 course_id 的文档
            count_result = await session.execute(
                select(func.count(RAGDocument.id))
                .where(RAGDocument.course_id == course_id)
            )
            total = count_result.scalar() or 0

            result = await session.execute(
                select(RAGDocument.doc_metadata)
                .where(RAGDocument.course_id == course_id)
                .distinct()
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            rows = result.scalars().all()

            items = []
            for doc_meta in rows:
                fname = None
                if doc_meta and isinstance(doc_meta, dict):
                    fname = doc_meta.get('filename')
                if fname:
                    # 计算该文件名下的文档数量（使用 Python 端过滤）
                    count_res = await session.execute(
                        select(func.count(RAGDocument.id))
                        .where(RAGDocument.course_id == course_id)
                    )
                    all_count = count_res.scalar() or 0
                    doc_count = 1  # 每个 doc_metadata 都是唯一的

                    items.append({
                        "doc_id": f"file_{fname}",
                        "filename": fname,
                        "course_id": course_id,
                        "doc_count": doc_count,
                        "doc_metadata": {"filename": fname},
                    })

    return {
        "code": 200,
        "message": "success",
        "data": {"items": items, "total": total, "page": page, "page_size": page_size},
    }


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """删除文档"""
    async with AsyncSessionLocal() as session:
        from sqlalchemy import delete
        await session.execute(delete(RAGDocument).where(RAGDocument.doc_id == doc_id))
        await session.commit()
        return {"code": 200, "message": "删除成功"}


@router.delete("/documents/by-filename/{filename}")
async def delete_documents_by_filename(filename: str):
    """按文件名删除所有相关文档块"""
    from sqlalchemy import delete, select, cast, String

    deleted_count = 0
    errors = []

    # 1. 从 PG 删除 RAGDocument - 通过 doc_metadata->>'filename' 匹配
    try:
        async with AsyncSessionLocal() as session:
            # 查询所有 doc_metadata->>'filename' 等于文件名的记录
            # PostgreSQL JSON 字段查询
            result = await session.execute(
                select(RAGDocument).where(
                    cast(RAGDocument.doc_metadata['filename'], String) == f'"{filename}"'
                )
            )
            docs_to_delete = result.scalars().all()
            doc_ids = [doc.doc_id for doc in docs_to_delete]

            if doc_ids:
                await session.execute(
                    delete(RAGDocument).where(RAGDocument.doc_id.in_(doc_ids))
                )
                await session.commit()
                deleted_count += len(doc_ids)
    except Exception as e:
        errors.append(f"PG删除失败: {str(e)}")

    # 2. 从向量库删除
    try:
        from services.knowledge.vector.main import delete_vector_documents_by_filename
        count = await delete_vector_documents_by_filename(filename)
        deleted_count += count
    except Exception as e:
        errors.append(f"向量库删除失败: {str(e)}")

    # 3. 从 ES 删除
    try:
        from services.knowledge.es_indexer.main import delete_es_documents_by_filename
        count = await delete_es_documents_by_filename(filename)
        deleted_count += count
    except Exception as e:
        errors.append(f"ES删除失败: {str(e)}")

    if errors:
        return {"code": 200, "message": f"部分删除完成: {'; '.join(errors)}", "data": {"deleted": deleted_count}}
    return {"code": 200, "message": f"删除成功，共删除 {deleted_count} 个文档块", "data": {"deleted": deleted_count}}


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


@router.post("/fetch")
async def fetch_url_document(
    url: str = Form(...),
    course_id: str = Form("default")
):
    """从 URL 抓取文档内容并入库"""
    import httpx

    print(f"[DEBUG fetch] url={url}, course_id={course_id}", flush=True)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
    }
    try:
        async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            raw_content = response.content
            content_type = response.headers.get("content-type", "").lower()
            print(f"[DEBUG fetch] status={response.status_code}, content-type={content_type}, size={len(raw_content)}", flush=True)
    except httpx.TimeoutException:
        raise HTTPException(status_code=408, detail="下载超时，请检查URL是否可访问")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"下载失败: HTTP {e.response.status_code}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"下载失败: {str(e)}")

    # 检测是否真的是 PDF（检查文件头魔数）
    if len(raw_content) < 5 or not raw_content[:5] == b'%PDF-':
        print(f"[DEBUG fetch] 非PDF内容，前100字节: {raw_content[:200]}", flush=True)
        # 可能是 HTML 或压缩流，尝试解码
        if b'<!doctype html' in raw_content[:200].lower() or b'<html' in raw_content[:200].lower():
            raise HTTPException(status_code=422, detail="arXiv 需要添加 /pdf/ 路径而非 /abs/ 路径，请使用如 https://arxiv.org/pdf/1706.03762.pdf")
        raise HTTPException(status_code=422, detail=f"下载内容不是PDF，当前为: {content_type}")

    from urllib.parse import urlparse, unquote
    parsed = urlparse(url)
    path = unquote(parsed.path)
    filename = path.split("/")[-1] if path else "downloaded_file"

    mime_to_ext = {
        "application/pdf": ".pdf",
        "application/msword": ".doc",
        "application/vnd.openxmlformats": ".docx",
        "text/plain": ".txt",
        "text/html": ".html",
        "application/html": ".html",
    }
    if "." not in filename:
        for mime, ext in mime_to_ext.items():
            if mime in content_type:
                filename += ext
                break
        else:
            filename += ".html"

    content = ""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext == "pdf":
        try:
            import pdfplumber, io
            with pdfplumber.open(io.BytesIO(raw_content)) as pdf:
                pages = []
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        pages.append(t)
                content = "\n\n".join(pages)
            if not content.strip():
                raise ValueError("PDF文本提取为空")
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"PDF解析失败: {e}")
    elif ext in ("html", "htm"):
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(raw_content, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            main = (soup.find("article") or soup.find("main")
                    or soup.find("div", class_=lambda c: c and ("content" in c or "article" in c))
                    or soup)
            content = main.get_text(separator="\n", strip=True) if main else soup.get_text(separator="\n", strip=True)
            if len(content) > 50000:
                content = content[:50000]
            if not content.strip():
                raise ValueError("网页文本提取为空")
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"HTML解析失败: {e}")
    else:
        try:
            content = raw_content.decode("utf-8")
        except UnicodeDecodeError:
            try:
                content = raw_content.decode("gbk")
            except Exception:
                content = raw_content.decode("utf-8", errors="ignore")

    if not content.strip():
        raise HTTPException(status_code=422, detail="提取内容为空，无法入库")

    # PDF 传原始字节（让 process_file_upload 内部解析）
    # HTML/文本 传文本内容
    bytes_to_send = raw_content if ext == "pdf" else content.encode("utf-8")
    result = await process_file_upload(bytes_to_send, filename, course_id)

    return {
        "code": 200,
        "message": "抓取成功",
        "data": {
            "filename": result["filename"],
            "doc_count": result["total_chunks"],
            "doc_ids": result["doc_ids"]
        }
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
                "tfidf_embedding",
                "bm25_search",
                "hybrid_search",
                "query_processor",
                "kimi_generator"
            ],
            "architecture": "simplified_rag",
            "description": "TF-IDF + BM25 混合检索系统"
        }
    }
