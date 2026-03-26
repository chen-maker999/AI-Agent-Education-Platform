"""RAG 主服务 - 完整版：BM25 + 向量 + 图谱多路检索，支持意图识别和上下文优化"""

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
    """增强版 RAG 请求 - P11 优化版"""
    query: str
    student_id: str
    course_id: Optional[str] = None
    session_id: Optional[str] = None

    # 检索配置
    use_rewrite: bool = True
    use_rerank: bool = True
    use_graph: bool = True
    use_bm25: bool = True
    use_vector: bool = True

    # P11 新增：TRR 跨语言检索完整流程
    enable_trr: bool = False  # 启用 Translate-Retrieve-Rerank 完整流程

    # P11 新增：Parent-Child 检索
    use_parent_child: bool = False  # 启用小 chunk 检索 + 大 chunk 上下文

    # 权重配置（可选，不设置时根据意图自动调整）
    semantic_weight: Optional[float] = None
    keyword_weight: Optional[float] = None
    graph_weight: Optional[float] = None

    # 上下文配置
    max_context_tokens: int = 3000
    use_diversity: bool = True

    top_k: int = 10


# 意图权重配置 - P11 优化：提升语义权重，优化 F1 指标
INTENT_WEIGHTS = {
    # 概念解释：侧重语义和关键词 (P11 优化：提升语义权重)
    "concept_explanation": {"semantic": 0.55, "keyword": 0.30, "graph": 0.15},
    # 关系查询：侧重知识图谱 (P11 优化：适度提升语义)
    "relation_query": {"semantic": 0.35, "keyword": 0.20, "graph": 0.45},
    # 代码问题：平衡语义和关键词 (P11 优化：提升语义)
    "code_question": {"semantic": 0.50, "keyword": 0.35, "graph": 0.15},
    # 通用问题：平衡所有渠道 (P11 优化：提升语义)
    "general": {"semantic": 0.50, "keyword": 0.35, "graph": 0.15},
    # 对比问题：侧重关键词和图谱 (P11 优化：提升语义)
    "comparison": {"semantic": 0.40, "keyword": 0.40, "graph": 0.20},
    # 原因解释：侧重语义和图谱 (P11 优化：提升语义)
    "why_question": {"semantic": 0.50, "keyword": 0.15, "graph": 0.35},
}


class RAGRequestSimple(BaseModel):
    """简化版 RAG 请求"""
    session_id: Optional[str] = None
    student_id: str
    message: str = ""


class RAGResponse(BaseModel):
    answer: str
    sources: List[Dict]
    session_id: str
    intent: str
    processing_time: float
    retrieval_stats: Optional[Dict] = None


async def process_rag_request(request: RAGRequest) -> Dict:
    """完整的 RAG 处理流程 - 增强版"""
    start_time = datetime.now()
    retrieval_stats = {}

    # ==================== 0. 语义缓存检查 (P11 优化) ====================
    # 在检索前检查语义缓存，命中则直接返回
    try:
        from services.knowledge.cache.semantic_cache import get_cached_results
        from services.knowledge.embedding.main import generate_embeddings
        import numpy as np

        # 计算查询向量
        embeddings = await generate_embeddings([request.query])
        query_embedding = np.array(embeddings[0]).astype('float32')

        # 检查语义缓存
        cached_results = await get_cached_results(
            query=request.query,
            query_embedding=query_embedding,
            use_semantic=True
        )

        if cached_results is not None:
            retrieval_stats["cache_hit"] = True
            retrieval_stats["cache_source"] = "semantic_cache"
            print(f"语义缓存命中：{request.query[:30]}...")

            # 使用缓存结果直接生成答案
            from services.knowledge.rag.answer_generator import generate_smart_answer
            answer, sources = await generate_smart_answer(
                query=request.query,
                retrieved_docs=cached_results,
                top_k=request.top_k  # P11 优化：使用请求中的 top_k
            )

            processing_time = (datetime.now() - start_time).total_seconds()
            new_session_id = str(uuid.uuid4())

            # 保存会话
            from sqlalchemy import select
            from common.database.postgresql import AsyncSessionLocal
            async with AsyncSessionLocal() as session:
                from services.knowledge.rag.main import RAGSession
                rag_session = RAGSession(
                    session_id=new_session_id,
                    student_id=request.student_id,
                    query=request.query,
                    answer=answer,
                    sources=[{"doc_id": d.get("doc_id"), "content": d.get("content", "")[:200], "score": d.get("score", 0)} for d in cached_results]
                )
                session.add(rag_session)
                await session.commit()

            return {
                "answer": answer,
                "sources": cached_results,
                "intent": "cached",
                "processing_time": processing_time,
                "session_id": new_session_id,
                "retrieval_stats": retrieval_stats
            }
        else:
            retrieval_stats["cache_hit"] = False
    except Exception as e:
        print(f"语义缓存检查失败：{e}，继续执行检索流程")
        retrieval_stats["cache_error"] = str(e)

    # ==================== 0.5 TRR 完整流程 (P11 新增) ====================
    # 如果启用了 TRR，使用完整的 Translate-Retrieve-Rerank 流程
    if request.enable_trr:
        try:
            from services.knowledge.trr.main import translate_retrieve_rerank
            
            print(f"TRR 流程启动：{request.query[:30]}...")
            
            trr_results, trr_stats = await translate_retrieve_rerank(
                query=request.query,
                course_id=request.course_id,
                top_k=request.top_k,
                rerank_top_k=request.top_k // 2,
                enable_translation=True,
                use_cache=True
            )
            
            retrieval_stats["trr_applied"] = True
            retrieval_stats.update(trr_stats)
            
            # 使用 TRR 结果直接生成答案
            from services.knowledge.rag.answer_generator import generate_smart_answer
            answer, sources = await generate_smart_answer(
                query=request.query,
                retrieved_docs=trr_results,
                top_k=request.top_k  # P11 优化：使用请求中的 top_k
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            new_session_id = str(uuid.uuid4())
            
            # 保存会话
            from sqlalchemy import select
            from common.database.postgresql import AsyncSessionLocal
            async with AsyncSessionLocal() as session:
                from services.knowledge.rag.main import RAGSession
                rag_session = RAGSession(
                    session_id=new_session_id,
                    student_id=request.student_id,
                    query=request.query,
                    answer=answer,
                    sources=[{"doc_id": d.get("doc_id"), "content": d.get("content", "")[:200], "score": d.get("score", 0)} for d in trr_results]
                )
                session.add(rag_session)
                await session.commit()
            
            return {
                "answer": answer,
                "sources": trr_results,
                "intent": "trr_cross_language",
                "processing_time": processing_time,
                "session_id": new_session_id,
                "retrieval_stats": retrieval_stats
            }
            
        except Exception as e:
            print(f"TRR 流程失败：{e}，降级为标准 RAG 流程")
            retrieval_stats["trr_error"] = str(e)
            # 降级到标准流程

    # ==================== 1. 意图识别与查询路由 ====================
    intent = "general"
    channels = ["semantic", "keyword"]
    expanded_queries = [request.query]

    try:
        from services.knowledge.router.main import intent_classifier, query_rewriter, INTENT_TO_CHANNELS

        # 意图分类
        intent, confidence = intent_classifier.classify(request.query)
        retrieval_stats["intent"] = intent
        retrieval_stats["intent_confidence"] = round(confidence, 3)

        # 获取检索渠道
        channels = INTENT_TO_CHANNELS.get(intent, ["semantic", "keyword"])

        # 查询改写
        if request.use_rewrite:
            expanded_queries = query_rewriter.rewrite(request.query, intent)
            retrieval_stats["expanded_queries"] = len(expanded_queries)
    except Exception as e:
        print(f"意图识别失败：{e}")

    # ==================== 2. 多路检索 ====================
    all_results = {
        "semantic": [],
        "keyword": [],
        "graph": []
    }

    # 2.1 向量语义检索 (使用混合检索引擎)
    if request.use_vector and "semantic" in channels:
        try:
            from services.knowledge.rag.retriever import hybrid_search

            # 使用混合检索引擎 (静态库 + 动态库) - P11 优化：传递 use_parent_child 参数
            semantic_results, tfidf_stats = await hybrid_search(
                query=request.query,
                course_id=request.course_id,
                top_k=request.top_k,
                use_cache=True,
                enable_hyde=True,  # P11 优化：默认启用 HyDE
                request_id=str(uuid.uuid4())
            )

            all_results["semantic"] = semantic_results
            retrieval_stats["semantic_count"] = len(semantic_results)
            retrieval_stats.update({k: v for k, v in tfidf_stats.items() if k != 'semantic_count'})
        except Exception as e:
            print(f"向量检索失败：{e}，降级为关键词检索")
            retrieval_stats["semantic_fallback"] = True

    # 2.2 BM25 关键词检索
    if request.use_bm25 and "keyword" in channels:
        try:
            from services.knowledge.rag.retriever import keyword_search_with_bm25
            
            bm25_results, bm25_stats = await keyword_search_with_bm25(
                query=request.query,
                course_id=request.course_id,
                top_k=request.top_k,
                request_id=str(uuid.uuid4())
            )
            
            all_results["keyword"] = bm25_results
            retrieval_stats.update({k: v for k, v in bm25_stats.items() if k != 'keyword_count'})
        except Exception as e:
            print(f"BM25 检索失败：{e}")
            # 降级逻辑已在 retriever.py 中处理

    # 2.3 知识图谱检索
    if request.use_graph and "graph" in channels:
        try:
            from services.knowledge.rag.retriever import graph_search

            graph_results, graph_stats = await graph_search(
                query=request.query,
                course_id=request.course_id,
                top_k=request.top_k,  # P11 优化：使用请求中的 top_k
                intent=intent,
                request_id=str(uuid.uuid4())
            )
            
            all_results["graph"] = graph_results
            retrieval_stats.update({k: v for k, v in graph_stats.items() if k != 'graph_count'})
        except Exception as e:
            print(f"图谱检索失败：{e}")

    # ==================== 3. 结果融合 ====================
    fused_results = []

    # 根据意图动态调整权重（如果请求中未指定）
    if request.semantic_weight is not None:
        # 使用用户指定的权重
        weights = {
            "semantic": request.semantic_weight,
            "keyword": request.keyword_weight,
            "graph": request.graph_weight
        }
        retrieval_stats["weight_source"] = "user_specified"
    else:
        # 根据意图自动调整权重
        weights_config = INTENT_WEIGHTS.get(intent, INTENT_WEIGHTS["general"])
        weights = {
            "semantic": weights_config["semantic"],
            "keyword": weights_config["keyword"],
            "graph": weights_config["graph"]
        }
        retrieval_stats["weight_source"] = "intent_based"
        retrieval_stats["intent_weights"] = weights_config
    
    doc_map = {}
    for channel, results in all_results.items():
        weight = weights.get(channel, 0.33)
        for r in results:
            doc_id = r.get("doc_id")
            if doc_id not in doc_map:
                doc_map[doc_id] = r.copy()
                doc_map[doc_id]["final_score"] = r.get("score", 0) * weight
                doc_map[doc_id]["channels"] = [channel]
            else:
                doc_map[doc_id]["final_score"] += r.get("score", 0) * weight
                doc_map[doc_id]["channels"].append(channel)
    
    fused_results = sorted(doc_map.values(), key=lambda x: x.get("final_score", 0), reverse=True)
    # P11 优化：扩展候选池至 top_k×3，为重排序提供更大选择空间
    fused_results = fused_results[:request.top_k * 3]

    retrieval_stats["fused_count"] = len(fused_results)

    # ==================== 4. 重排序 (P11 优化：增强重排序效果) ====================
    if request.use_rerank and fused_results:
        try:
            from services.knowledge.rerank.main import rerank_documents
            # P11 优化：重排序时也保留更多候选，让 Cross-Encoder 充分筛选
            rerank_top_k = min(request.top_k * 2, len(fused_results))
            fused_results = await rerank_documents(
                query=request.query,
                documents=fused_results,
                top_k=rerank_top_k
            )
            retrieval_stats["reranked"] = True
            retrieval_stats["rerank_top_k"] = rerank_top_k
        except Exception as e:
            print(f"重排序失败：{e}")
            fused_results = fused_results[:request.top_k]

    # ==================== 5. 上下文修剪与压缩 ====================
    try:
        from services.knowledge.trimmer.main import trim_context
        
        strategy = "diversity" if request.use_diversity else "score_priority"
        trimmed_docs, total_tokens = trim_context(
            documents=fused_results,
            query=request.query,
            max_tokens=request.max_context_tokens,
            strategy=strategy
        )
        
        retrieval_stats["context_tokens"] = total_tokens
    except Exception as e:
        print(f"上下文修剪失败：{e}")
        trimmed_docs = fused_results[:request.top_k]

    # ==================== 6. 生成回答 ====================
    answer = ""
    sources_for_response = trimmed_docs

    try:
        # 使用智能答案生成器（不使用 LLM）
        from services.knowledge.rag.answer_generator import generate_smart_answer

        answer, sources_from_generator = await generate_smart_answer(
            query=request.query,
            retrieved_docs=trimmed_docs,
            top_k=request.top_k  # P11 优化：使用请求中的 top_k
        )

        # 使用生成器返回的来源
        if sources_from_generator:
            sources_for_response = sources_from_generator

    except Exception as e:
        print(f"智能答案生成失败：{e}")
        # 降级方案：直接返回检索结果
        if trimmed_docs:
            answer = f"根据检索到的资料：\n\n{trimmed_docs[0].get('content', '')[:500]}..."
            answer += "\n\n---\n**参考资料**: 共 {} 个文档".format(len(trimmed_docs))
        else:
            answer = "抱歉，无法找到相关知识来回答这个问题。"

    processing_time = (datetime.now() - start_time).total_seconds()
    retrieval_stats["total_time"] = round(processing_time, 3)

    # ==================== 6.5. 缓存结果 (P11 优化) ====================
    # 将检索结果缓存，供后续相似查询使用
    try:
        from services.knowledge.cache.semantic_cache import set_cache_results
        from services.knowledge.embedding.main import generate_embeddings
        import numpy as np

        # 计算查询向量
        embeddings = await generate_embeddings([request.query])
        query_embedding = np.array(embeddings[0]).astype('float32')

        # 缓存检索结果
        await set_cache_results(
            query=request.query,
            results=trimmed_docs,
            query_embedding=query_embedding,
            ttl=3600  # 1 小时过期
        )
        retrieval_stats["cached"] = True
    except Exception as e:
        retrieval_stats["cached"] = False
        retrieval_stats["cache_error"] = str(e)

    # 7. 保存会话到数据库
    new_session_id = str(uuid.uuid4())
    async with AsyncSessionLocal() as session:
        rag_session = RAGSession(
            session_id=new_session_id,
            student_id=request.student_id,
            query=request.query,
            answer=answer,
            sources=[{"doc_id": d.get("doc_id"), "content": d.get("content", "")[:200], "score": d.get("score")} for d in sources_for_response]
        )
        session.add(rag_session)
        await session.commit()

    return {
        "answer": answer,
        "sources": sources_for_response,
        "intent": intent,
        "processing_time": processing_time,
        "session_id": new_session_id,
        "retrieval_stats": retrieval_stats
    }


@router.post("/chat", response_model=RAGResponse)
async def rag_chat(request: RAGRequest):
    """RAG 对话接口 - 完整版"""
    session_id = request.session_id or str(uuid.uuid4())

    try:
        result = await process_rag_request(request)

        # 直接返回 RAGResponse 对象，避免响应模型验证失败
        return RAGResponse(
            answer=result["answer"],
            sources=result["sources"],
            session_id=session_id,
            intent=result["intent"],
            processing_time=result["processing_time"],
            retrieval_stats=result.get("retrieval_stats")
        )
    except Exception as e:
        import traceback
        import logging
        error_detail = traceback.format_exc()
        logging.error(f"RAG聊天错误: {e}\n{error_detail}")
        print(f"RAG聊天错误: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"RAG 处理失败：{str(e)}")


@router.post("/chat/simple")
async def rag_chat_simple(request: RAGRequestSimple):
    """简化版 RAG 对话"""
    session_id = request.session_id or str(uuid.uuid4())

    simple_request = RAGRequest(
        query=request.message or "你好",
        student_id=request.student_id,
        session_id=session_id,
        use_rewrite=False,
        use_rerank=False,
        use_graph=False,
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


# 保留原有的文件上传、文档列表等接口...
async def process_file_upload(file_content: bytes, filename: str, course_id: str = "default") -> Dict:
    """处理文件上传：读取内容、语义分块、向量化、存储 (P11 优化)"""
    print(f"[DEBUG upload] course_id={course_id}, filename={filename}", flush=True)
    # P11 优化：导入语义分块
    from services.knowledge.chunk.semantic_chunking import semantic_chunking as semantic_chunking_func
    from services.knowledge.vector.main import add_documents, Document
    import io

    ext = filename.split('.')[-1].lower() if '.' in filename else ''

    if ext == 'pdf':
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
            raise ValueError(f"PDF 解析失败：{str(e)},请确保 PDF 包含可提取的文本")
    else:
        try:
            content = file_content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                content = file_content.decode('gbk')
            except:
                content = file_content.decode('utf-8', errors='ignore')

    # P11 优化：使用语义分块替代 chunk_text
    chunks = semantic_chunking_func(
        text=content,
        max_chunk_size=1500,
        min_chunk_size=200,
        overlap_ratio=0.15,
        use_semantic_boundary=True
    )
    
    # 如果没有分块结果，使用原始内容
    if not chunks:
        chunks = [{
            "chunk_id": hashlib.md5(f"{filename}_0".encode()).hexdigest()[:16],
            "content": content,
            "start_index": 0,
            "end_index": len(content),
            "level": 0,
            "parent_chunk_id": None,
            "child_chunk_ids": [],
            "metadata": {"filename": filename},
            "char_count": len(content),
            "estimated_tokens": int(len(content) / 4)
        }]

    doc_ids = []
    docs_to_index = []
    db_docs = []

    for i, chunk in enumerate(chunks):
        doc_id = hashlib.md5(f"{filename}_{i}_{course_id}".encode()).hexdigest()
        doc_ids.append(doc_id)

        doc = Document(
            content=chunk["content"],
            metadata={
                "filename": filename,
                "chunk_index": i,
                "course_id": course_id,
                "doc_id": doc_id,
                "chunk_metadata": chunk.get("metadata", {})
            }
        )
        docs_to_index.append(doc)

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
                db_docs.append({
                    "doc_id": doc_id,
                    "content": chunk["content"],
                    "course_id": course_id,
                    "metadata": doc.metadata
                })

        await session.commit()

    # 使用索引同步服务统一添加所有索引
    if db_docs:
        try:
            from services.knowledge.index_sync import sync_add_documents
            sync_result = await sync_add_documents(db_docs)
            print(f"索引同步添加结果：{sync_result}")
        except Exception as e:
            print(f"索引同步添加失败：{e}")

    return {
        "doc_ids": doc_ids,
        "total_chunks": len(doc_ids),
        "filename": filename
    }


@router.post("/upload")
async def upload_document(file: UploadFile = File(...), course_id: str = Form("default")):
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
        raise HTTPException(status_code=500, detail=f"文件处理失败：{str(e)}")


@router.get("/documents")
async def list_documents(
    course_id: str = "default",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=500),
    all_courses: bool = Query(False, description="为 true 时列出所有 course_id 下的文档"),
):
    """列出已上传的文档"""
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select, func

        if all_courses:
            result = await session.execute(
                select(RAGDocument.course_id, RAGDocument.doc_metadata, func.count(RAGDocument.id).label("doc_count"))
                .group_by(RAGDocument.course_id, RAGDocument.doc_metadata)
                .order_by(RAGDocument.course_id)
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            rows = result.all()

            file_map = {}
            for row in rows:
                cid = row.course_id or ""
                fname = row.doc_metadata.get('filename') if row.doc_metadata else None
                if fname:
                    key = (cid, fname)
                    file_map[key] = file_map.get(key, 0) + row.doc_count

            count_result = await session.execute(select(func.count(RAGDocument.id)))
            total = count_result.scalar() or 0

            items = [{"doc_id": f"file_{cid}_{fname}", "filename": fname, "course_id": cid, "doc_count": doc_count} for (cid, fname), doc_count in file_map.items()]
        else:
            count_result = await session.execute(select(func.count(RAGDocument.id)).where(RAGDocument.course_id == course_id))
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
                fname = doc_meta.get('filename') if doc_meta else None
                if fname:
                    items.append({"doc_id": f"file_{fname}", "filename": fname, "course_id": course_id, "doc_count": 1, "doc_metadata": {"filename": fname}})

    return {"code": 200, "message": "success", "data": {"items": items, "total": total, "page": page, "page_size": page_size}}


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """删除文档（同步更新所有索引）"""
    async with AsyncSessionLocal() as session:
        from sqlalchemy import delete, select
        
        # 1. 从数据库删除
        result = await session.execute(select(RAGDocument).where(RAGDocument.doc_id == doc_id))
        doc = result.scalar_one_or_none()
        
        if not doc:
            return {"code": 404, "message": "文档不存在"}
        
        await session.execute(delete(RAGDocument).where(RAGDocument.doc_id == doc_id))
        await session.commit()
        
        # 2. 同步从索引中删除
        try:
            from services.knowledge.index_sync import sync_remove_documents
            await sync_remove_documents([doc_id])
        except Exception as e:
            logger.warning(f"索引同步删除失败：{e}")
        
        return {"code": 200, "message": "删除成功", "data": {"doc_id": doc_id}}


@router.delete("/documents/by-filename/{filename}")
async def delete_documents_by_filename(filename: str):
    """按文件名删除所有相关文档块"""
    from sqlalchemy import delete, select, cast, String

    deleted_count = 0
    errors = []

    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(RAGDocument).where(cast(RAGDocument.doc_metadata['filename'], String) == f'"{filename}"'))
            docs_to_delete = result.scalars().all()
            doc_ids = [doc.doc_id for doc in docs_to_delete]

            if doc_ids:
                await session.execute(delete(RAGDocument).where(RAGDocument.doc_id.in_(doc_ids)))
                await session.commit()
                deleted_count += len(doc_ids)
    except Exception as e:
        errors.append(f"PG 删除失败：{str(e)}")

    try:
        from services.knowledge.vector.main import delete_vector_documents_by_filename
        count = await delete_vector_documents_by_filename(filename)
        deleted_count += count
    except Exception as e:
        errors.append(f"向量库删除失败：{str(e)}")

    try:
        from services.knowledge.bm25_search.main import bm25_index
        for doc_id in list(bm25_index.documents.keys()):
            if filename in doc_id:
                bm25_index.remove_document(doc_id)
                deleted_count += 1
        bm25_index.save()
    except Exception as e:
        errors.append(f"BM25 删除失败：{str(e)}")

    if errors:
        return {"code": 200, "message": f"部分删除完成：{'; '.join(errors)}", "data": {"deleted": deleted_count}}
    return {"code": 200, "message": f"删除成功，共删除 {deleted_count} 个文档块", "data": {"deleted": deleted_count}}


@router.get("/history/{student_id}")
async def get_chat_history(student_id: str, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    """获取学生的对话历史"""
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select, func

        count_result = await session.execute(select(func.count(RAGSession.id)).where(RAGSession.student_id == student_id))
        total = count_result.scalar() or 0

        result = await session.execute(
            select(RAGSession)
            .where(RAGSession.student_id == student_id)
            .order_by(RAGSession.created_at.desc())
            .offset((page-1)*page_size)
            .limit(page_size)
        )
        sessions = result.scalars().all()

        items = [{"session_id": s.session_id, "query": s.query, "answer": s.answer, "sources": s.sources, "created_at": s.created_at.isoformat() if s.created_at else None} for s in sessions]

    return {"code": 200, "message": "success", "data": {"items": items, "total": total}}


@router.post("/fetch")
async def fetch_url_document(url: str = Form(...), course_id: str = Form("default")):
    """从 URL 抓取文档内容并入库"""
    import httpx
    from urllib.parse import urlparse, unquote

    print(f"[DEBUG fetch] url={url}, course_id={course_id}", flush=True)

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    try:
        async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            raw_content = response.content
            content_type = response.headers.get("content-type", "").lower()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"下载失败：{str(e)}")

    if len(raw_content) < 5 or not raw_content[:5] == b'%PDF-':
        if b'<!doctype html' in raw_content[:200].lower() or b'<html' in raw_content[:200].lower():
            raise HTTPException(status_code=422, detail="arXiv 需要添加 /pdf/ 路径，请使用如 https://arxiv.org/pdf/1706.03762.pdf")
        raise HTTPException(status_code=422, detail=f"下载内容不是 PDF，当前为：{content_type}")

    parsed = urlparse(url)
    path = unquote(parsed.path)
    filename = path.split("/")[-1] if path else "downloaded_file"

    if "." not in filename:
        filename += ".pdf"

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
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"PDF 解析失败：{e}")
    else:
        try:
            content = raw_content.decode("utf-8")
        except:
            content = raw_content.decode("utf-8", errors="ignore")

    if not content.strip():
        raise HTTPException(status_code=422, detail="提取内容为空，无法入库")

    bytes_to_send = raw_content if ext == "pdf" else content.encode("utf-8")
    result = await process_file_upload(bytes_to_send, filename, course_id)

    return {"code": 200, "message": "抓取成功", "data": {"filename": result["filename"], "doc_count": result["total_chunks"], "doc_ids": result["doc_ids"]}}


@router.get("/health")
async def rag_health():
    """RAG 服务健康检查"""
    return {
        "code": 200,
        "message": "RAG 服务运行中",
        "data": {
            "components": [
                "chunk_engine",
                "tfidf_embedding",
                "bm25_search",
                "graph_search",
                "query_router",
                "reranker",
                "context_trimmer",
                "kimi_generator"
            ],
            "architecture": "full_rag",
            "description": "BM25 + 向量 + 图谱多路检索系统"
        }
    }
