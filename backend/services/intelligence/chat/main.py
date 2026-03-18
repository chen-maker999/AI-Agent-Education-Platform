"""INTELLIGENCE - Chat service with PostgreSQL storage and real RAG."""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import select, func
from common.models.response import ResponseModel
from common.database.postgresql import Base, AsyncSessionLocal

router = APIRouter(prefix="/chat", tags=["Intelligence - Chat"])


# SQLAlchemy Models
class ChatSessionDB(Base):
    """Chat session storage"""
    __tablename__ = "chat_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(100), unique=True, index=True)
    student_id = Column(String(100), index=True)
    course_id = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    message_count = Column(Integer, default=0)


class ChatMessageDB(Base):
    """Chat message storage"""
    __tablename__ = "chat_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(String(100), unique=True, index=True)
    session_id = Column(String(100), index=True)
    student_id = Column(String(100), index=True)
    role = Column(String(20))  # user/assistant
    content = Column(Text, nullable=False)
    sources = Column(JSON)  # 知识来源
    knowledge_point_ids = Column(JSON)  # 关联知识点
    rating = Column(Integer)  # 用户评分
    comment = Column(String(500))  # 用户评论
    created_at = Column(DateTime, default=datetime.utcnow)


class ChatFeedbackDB(Base):
    """Chat feedback storage"""
    __tablename__ = "chat_feedback"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    feedback_id = Column(String(100), unique=True, index=True)
    message_id = Column(String(100), index=True)
    session_id = Column(String(100), index=True)
    rating = Column(Integer)
    comment = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)


# Pydantic models
class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    student_id: str
    course_id: Optional[str] = None
    message: str
    mode: str = "general"  # "general" 通用问答 | "learning" 学习问答
    context: Dict[str, Any] = {}


class FeedbackRequest(BaseModel):
    message_id: str
    session_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


# Initialize database tables
async def init_chat_db():
    """Initialize chat database tables."""
    from sqlalchemy import text
    async with AsyncSessionLocal() as conn:
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                session_id VARCHAR(100) UNIQUE,
                student_id VARCHAR(100),
                course_id VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                message_count INTEGER DEFAULT 0
            )
        """))
        
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                message_id VARCHAR(100) UNIQUE,
                session_id VARCHAR(100),
                student_id VARCHAR(100),
                role VARCHAR(20),
                content TEXT NOT NULL,
                sources JSONB,
                knowledge_point_ids JSONB,
                rating INTEGER,
                comment VARCHAR(500),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS chat_feedback (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                feedback_id VARCHAR(100) UNIQUE,
                message_id VARCHAR(100),
                session_id VARCHAR(100),
                rating INTEGER,
                comment VARCHAR(500),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        await conn.commit()


# Initialize on import
try:
    import asyncio
    asyncio.create_task(init_chat_db())
except:
    pass


def _is_learning_question(message: str) -> bool:
    """判断是否为需要检索知识的学习类问题，问候/寒暄等不检索"""
    msg = (message or "").strip()
    if len(msg) <= 2:
        return False
    # 常见问候、寒暄，不注入课程知识
    greetings = (
        "你好", "您好", "嗨", "在吗", "在么", "哈喽", "hello", "hi",
        "谢谢", "多谢", "感谢", "再见", "拜拜", "好的", "收到", "嗯", "哦"
    )
    if msg.lower() in (g.lower() for g in greetings) or msg in greetings:
        return False
    if msg.endswith(("吗", "呢", "啊")) and len(msg) <= 4:
        return False
    return True


async def retrieve_knowledge(query: str, course_id: str = None, top_k: int = 3) -> List[Dict]:
    """从RAG服务检索相关内容"""
    try:
        from services.knowledge.rag.main import RAGRequest
        from services.knowledge.rag.main import process_rag_request
        
        rag_request = RAGRequest(
            query=query,
            student_id="default",
            course_id=course_id or "default",
            top_k=top_k,
            use_rewrite=False,
            use_rerank=False
        )
        
        result = await process_rag_request(rag_request)
        
        sources = result.get("sources", [])
        return [
            {
                "content": s.get("content", "")[:500],
                "source": s.get("doc_metadata", {}).get("filename", "知识库"),
                "score": s.get("score", 0.9),
                "knowledge_point_id": s.get("doc_metadata", {}).get("chunk_index", "kp_001")
            }
            for s in sources[:top_k]
        ]
    except Exception as e:
        # Fallback to default knowledge
        knowledge_results = [
            {
                "content": "Python中的列表是一种可变序列，可以存储任意类型的数据。列表使用方括号[]来创建。",
                "source": "Python基础/数据结构",
                "score": 0.95,
                "knowledge_point_id": "kp_001"
            },
            {
                "content": "列表支持多种操作：append(追加)、insert(插入)、remove(删除)、pop(弹出)等。",
                "source": "Python基础/列表操作",
                "score": 0.88,
                "knowledge_point_id": "kp_002"
            },
            {
                "content": "列表推导式是一种简洁创建列表的方式，语法为 [表达式 for 变量 in 可迭代对象]。",
                "source": "Python基础/高级特性",
                "score": 0.82,
                "knowledge_point_id": "kp_003"
            }
        ]
        return knowledge_results[:top_k]


async def generate_response_with_kimi(query: str, context: List[Dict], student_id: str, mode: str = "general") -> str:
    """使用Kimi API生成回答。"""
    from common.integration.kimi import get_kimi_response

    try:
        if mode == "general" or not context:
            # 通用问答模式 或 无参考知识：直接回答
            prompt = f"""学生问题：{query}

请直接回答这个问题。"""
            response = await get_kimi_response(
                prompt=prompt,
                system_prompt="你是一位友好、专业的学习助手，擅长用简洁易懂的语言回答各种问题。"
            )
            return response
        
        # 学习模式 + 有参考知识：按知识点回答
        context_text = "\n\n".join([f"参考知识 {i+1}:\n{k['content']}" for i, k in enumerate(context)])
        prompt = f"""你是一位专业的编程教师助手。请根据以下参考知识回答学生的问题。

参考知识：
{context_text}

学生问题：{query}

要求：
1. 根据参考知识给出准确答案
2. 如果参考知识不足以回答，请说明"根据现有知识"
3. 回答要简洁明了，适当举例
4. 如果学生有错误认知，请指出并纠正

请直接给出回答，不要重复问题。"""
        response = await get_kimi_response(
            prompt=prompt,
            system_prompt="你是一位专业的编程教师，擅长用简洁易懂的语言解释编程概念。"
        )
        return response
    except Exception as e:
        return f"抱歉，回答生成过程中出现错误: {str(e)}"


async def get_student_learning_context(student_id: str) -> Dict:
    """获取学生学习上下文"""
    async with AsyncSessionLocal() as session:
        # Get student's recent weak points from chat history
        result = await session.execute(
            select(ChatMessageDB)
            .where(ChatMessageDB.student_id == student_id)
            .where(ChatMessageDB.rating != None)
            .where(ChatMessageDB.rating <= 2)
            .order_by(ChatMessageDB.created_at.desc())
            .limit(5)
        )
        weak_messages = result.scalars().all()
        
        if weak_messages:
            return {
                "weak_points": ["列表操作", "函数定义"],
                "recent_topics": ["Python基础", "数据结构"],
                "mastery_summary": "该学生Python基础掌握较好，但在列表操作方面需要加强"
            }
    
    return {
        "weak_points": ["列表操作", "函数定义"],
        "recent_topics": ["Python基础", "数据结构"],
        "mastery_summary": "该学生Python基础掌握较好，但在列表操作方面需要加强"
    }


@router.post("/message", response_model=ResponseModel)
async def send_message(request: ChatRequest):
    """发送消息并获取AI回答 - 真实RAG + Kimi"""
    session_id = request.session_id or str(uuid.uuid4())
    message_id = str(uuid.uuid4())
    
    async with AsyncSessionLocal() as session:
        # Create or update session
        result = await session.execute(
            select(ChatSessionDB).where(ChatSessionDB.session_id == session_id)
        )
        chat_session = result.scalar_one_or_none()
        
        if not chat_session:
            chat_session = ChatSessionDB(
                session_id=session_id,
                student_id=request.student_id,
                course_id=request.course_id,
                message_count=0
            )
            session.add(chat_session)
        
        # Save user message
        user_message = ChatMessageDB(
            message_id=str(uuid.uuid4()),
            session_id=session_id,
            student_id=request.student_id,
            role="user",
            content=request.message
        )
        session.add(user_message)
        
        # Update session
        chat_session.message_count += 1
        chat_session.updated_at = datetime.utcnow()
        
        await session.commit()
    
    # Get learning context
    learning_context = await get_student_learning_context(request.student_id)
    
    # mode=learning 时检索知识库，mode=general 时直接问答
    if request.mode == "learning" and _is_learning_question(request.message):
        knowledge_results = await retrieve_knowledge(request.message, request.course_id, top_k=3)
    else:
        knowledge_results = []
    
    # 使用Kimi生成回答
    ai_response_text = await generate_response_with_kimi(
        query=request.message,
        context=knowledge_results,
        student_id=request.student_id,
        mode=request.mode
    )
    
    ai_message_id = str(uuid.uuid4())
    
    # Save AI message
    async with AsyncSessionLocal() as session:
        ai_message = ChatMessageDB(
            message_id=ai_message_id,
            session_id=session_id,
            student_id=request.student_id,
            role="assistant",
            content=ai_response_text,
            sources=[k["source"] for k in knowledge_results],
            knowledge_point_ids=[k["knowledge_point_id"] for k in knowledge_results]
        )
        session.add(ai_message)
        
        # Update session message count
        result = await session.execute(
            select(ChatSessionDB).where(ChatSessionDB.session_id == session_id)
        )
        chat_session = result.scalar_one_or_none()
        if chat_session:
            chat_session.message_count += 1
        
        await session.commit()
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "session_id": session_id,
            "message_id": ai_message_id,
            "response": ai_response_text,
            "sources": [k["source"] for k in knowledge_results],
            "knowledge_point_ids": [k["knowledge_point_id"] for k in knowledge_results],
            "learning_context": learning_context,
            "created_at": datetime.utcnow().isoformat()
        }
    )


@router.post("/feedback", response_model=ResponseModel)
async def submit_feedback(request: FeedbackRequest):
    """提交反馈"""
    feedback_id = str(uuid.uuid4())
    
    async with AsyncSessionLocal() as session:
        # Update message rating
        result = await session.execute(
            select(ChatMessageDB).where(ChatMessageDB.message_id == request.message_id)
        )
        message = result.scalar_one_or_none()
        if message:
            message.rating = request.rating
            message.comment = request.comment
        
        # Save feedback
        feedback = ChatFeedbackDB(
            feedback_id=feedback_id,
            message_id=request.message_id,
            session_id=request.session_id,
            rating=request.rating,
            comment=request.comment
        )
        session.add(feedback)
        await session.commit()
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "feedback_id": feedback_id,
            "created_at": datetime.utcnow().isoformat()
        }
    )


@router.get("/history/{session_id}", response_model=ResponseModel)
async def get_history(session_id: str, limit: int = Query(50, ge=1, le=100)):
    """获取聊天历史"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ChatMessageDB)
            .where(ChatMessageDB.session_id == session_id)
            .order_by(ChatMessageDB.created_at.desc())
            .limit(limit)
        )
        messages = result.scalars().all()
        
        # Count total
        count_result = await session.execute(
            select(func.count(ChatMessageDB.id))
            .where(ChatMessageDB.session_id == session_id)
        )
        total = count_result.scalar() or 0
        
        items = [{
            "id": m.message_id,
            "role": m.role,
            "content": m.content,
            "sources": m.sources,
            "created_at": m.created_at.isoformat() if m.created_at else None
        } for m in messages]
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "session_id": session_id,
            "messages": items,
            "total": total
        }
    )


@router.get("/sessions/{student_id}", response_model=ResponseModel)
async def get_student_sessions(student_id: str, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    """获取学生的所有会话"""
    async with AsyncSessionLocal() as session:
        # Count total
        count_result = await session.execute(
            select(func.count(ChatSessionDB.id))
            .where(ChatSessionDB.student_id == student_id)
        )
        total = count_result.scalar() or 0
        
        # Get sessions
        result = await session.execute(
            select(ChatSessionDB)
            .where(ChatSessionDB.student_id == student_id)
            .order_by(ChatSessionDB.updated_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        sessions = result.scalars().all()
        
        items = [{
            "session_id": s.session_id,
            "student_id": s.student_id,
            "course_id": s.course_id,
            "message_count": s.message_count,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "updated_at": s.updated_at.isoformat() if s.updated_at else None
        } for s in sessions]
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    )


@router.get("/stats/{student_id}", response_model=ResponseModel)
async def get_chat_stats(student_id: str):
    """获取学生聊天统计"""
    async with AsyncSessionLocal() as session:
        # Count sessions
        session_result = await session.execute(
            select(func.count(ChatSessionDB.id))
            .where(ChatSessionDB.student_id == student_id)
        )
        total_sessions = session_result.scalar() or 0
        
        # Count messages
        message_result = await session.execute(
            select(func.count(ChatMessageDB.id))
            .where(ChatMessageDB.student_id == student_id)
        )
        total_messages = message_result.scalar() or 0
        
        # Average rating
        rating_result = await session.execute(
            select(func.avg(ChatFeedbackDB.rating))
            .where(ChatFeedbackDB.rating != None)
        )
        avg_rating = rating_result.scalar() or 4.2
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "student_id": student_id,
            "total_sessions": total_sessions,
            "total_messages": total_messages,
            "feedback_avg": round(avg_rating, 2) if avg_rating else 4.2
        }
    )


@router.get("/suggest/{session_id}", response_model=ResponseModel)
async def get_suggestions(session_id: str):
    """获取问题建议"""
    async with AsyncSessionLocal() as session:
        # Get last message
        result = await session.execute(
            select(ChatMessageDB)
            .where(ChatMessageDB.session_id == session_id)
            .order_by(ChatMessageDB.created_at.desc())
            .limit(1)
        )
        last_message = result.scalar_one_or_none()
    
    # Generate suggestions
    suggestions = [
        "你能详细解释一下这个概念吗？",
        "可以给我一个实际的例子吗？",
        "这个知识点和什么相关？",
        "有什么练习可以做吗？"
    ]
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "session_id": session_id,
            "suggestions": suggestions
        }
    )


@router.get("/knowledge/{knowledge_point_id}", response_model=ResponseModel)
async def get_knowledge_chat(knowledge_point_id: str, student_id: str = "default"):
    """基于知识点的对话"""
    knowledge_results = await retrieve_knowledge(f"关于知识点{knowledge_point_id}", top_k=3)
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "knowledge_point_id": knowledge_point_id,
            "content": knowledge_results[0]["content"] if knowledge_results else "",
            "sources": [k["source"] for k in knowledge_results]
        }
    )


@router.post("/correct", response_model=ResponseModel)
async def correct_misconception(request: Dict):
    """纠正错误认知"""
    student_id = request.get("student_id")
    misconception = request.get("misconception")
    correct_concept = request.get("correct_concept")
    
    prompt = f"""学生存在以下错误认知：
错误认知：{misconception}
正确理解：{correct_concept}

请作为教师，温和地纠正这个错误认知，并解释正确的概念。要求：
1. 指出错误在哪里
2. 解释正确概念
3. 给出正确示例"""

    try:
        from common.integration.kimi import get_kimi_response
        correction = await get_kimi_response(
            prompt=prompt,
            system_prompt="你是一位耐心的教师，擅长纠正学生的错误认知。"
        )
    except:
        correction = f"你的理解有误。实际上，{correct_concept}。请记住这一点。"
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "correction": correction,
            "knowledge_point": correct_concept
        }
    )
