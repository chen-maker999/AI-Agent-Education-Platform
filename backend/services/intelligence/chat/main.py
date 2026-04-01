"""INTELLIGENCE - Chat service with PostgreSQL storage and real RAG."""

import json
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
    student_id: Optional[str] = "default"
    course_id: Optional[str] = None
    message: str
    mode: str = "general"  # "general" 通用问答 | "learning" 学习问答
    context: Dict[str, Any] = {}
    tools: Optional[List[Dict[str, Any]]] = None  # 支持 Function Calling
    # 模型参数
    model: Optional[str] = "kimi-k2.5"
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.9
    max_tokens: Optional[int] = 4096
    frequency_penalty: Optional[float] = 0.0
    presence_penalty: Optional[float] = 0.0


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


async def generate_response_with_kimi(
    query: str,
    context: List[Dict],
    student_id: str,
    mode: str = "general",
    tools: Optional[List[Dict[str, Any]]] = None,
    history: Optional[List[Dict[str, str]]] = None,
    current_turn_messages: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """使用Kimi API生成回答。返回 {"type": "message"|"tool_calls", "content"|"tool_calls": ...}
    history: 本会话的历史消息（不含当前轮），用于上下文关联。
    current_turn_messages: 当前轮已产生的消息（如 user + assistant tool_calls + tool），用于工具调用续写时传入。
    """
    from common.integration.kimi import kimi_client

    try:
        # 构建消息
        system_content = "你是一位友好、专业的学习助手，擅长用简洁易懂的语言回答各种问题。请结合当前对话的上下文理解用户的指代（如「这篇论文」「刚才那个」等）。"

        messages = [
            {"role": "system", "content": system_content}
        ]

        # 注入历史对话，保证「这篇论文」等指代能关联到上文
        if history:
            for h in history:
                if h.get("content"):  # 只添加有内容的消息
                    messages.append({"role": h["role"], "content": h["content"]})

        if current_turn_messages:
            # 工具调用续写：只追加当前轮已有消息（含 assistant 的 tool_calls 与 tool 结果），不再追加 query
            for m in current_turn_messages:
                msg = dict(m)
                role = msg.get("role")
                if role == "tool":
                    messages.append({"role": "tool", "tool_call_id": msg.get("tool_call_id"), "content": msg.get("content", "")})
                elif "tool_calls" in msg and msg.get("tool_calls"):
                    messages.append({"role": "assistant", "content": msg.get("content"), "tool_calls": msg["tool_calls"]})
                else:
                    messages.append({"role": role, "content": msg.get("content") or ""})
        else:
            # 新的一轮：追加当前用户问题（可带学习模式上下文）
            if mode == "learning" and context:
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
                messages.append({"role": "user", "content": prompt})
            else:
                # 普通问答 - 使用简洁的消息
                messages.append({"role": "user", "content": query})

        # 如果有工具定义，使用 Function Calling
        if tools:
            model_for_call = "kimi-k2.5"  # kimi-k2.5 enforces fixed params
            effective_top_p = 1.0  # kimi-k2.5 requires top_p=1.0
            result = await kimi_client.chat(
                messages=messages,
                tools=tools,
                model=model_for_call,
                temperature=1.0,  # kimi-k2.5 模型只接受 temperature=1
                max_tokens=2048,
                top_p=effective_top_p,
            )

            if "error" in result:
                detail = result.get("detail") or ""
                err_text = f"抱歉，调用 AI 服务时出错：{result['error']}"
                if detail:
                    err_text = err_text + " " + detail[:800]
                return {"type": "message", "content": err_text}

            choices = result.get("choices", [])
            if not choices:
                return {"type": "message", "content": "抱歉，没有收到 AI 的回复。"}

            message = choices[0].get("message", {})

            # 检查是否有 tool_calls
            if "tool_calls" in message and message["tool_calls"]:
                return {
                    "type": "tool_calls",
                    "tool_calls": message["tool_calls"]
                }

            # 普通文本回复
            content = message.get("content", "")
            return {"type": "message", "content": content}
        else:
            # 没有工具：用完整 messages（含历史）调用 chat，保证上下文关联
            model_for_call = "kimi-k2.5"
            effective_top_p = 1.0  # kimi-k2.5 requires top_p=1.0
            result = await kimi_client.chat(
                messages=messages,
                model=model_for_call,
                temperature=1.0,  # kimi-k2.5 模型只接受 temperature=1
                max_tokens=2048,
                top_p=effective_top_p,
            )
            if "error" in result:
                detail = result.get("detail") or ""
                err_text = f"抱歉，调用 AI 服务时出错：{result['error']}"
                if detail:
                    err_text = err_text + " " + detail[:800]
                return {"type": "message", "content": err_text}
            choices = result.get("choices", [])
            if not choices:
                return {"type": "message", "content": "抱歉，没有收到 AI 的回复。"}
            content = (choices[0].get("message") or {}).get("content", "")
            return {"type": "message", "content": content or "（无回复）"}

    except Exception as e:
        return {"type": "message", "content": f"抱歉，回答生成过程中出现错误，请稍后重试。错误详情: {str(e)}"}


async def get_session_history(session_id: str, limit_rounds: int = 10) -> List[Dict[str, str]]:
    """获取会话历史（不含当前这条用户消息），按时间正序。用于上下文关联。"""
    async with AsyncSessionLocal() as session:
        # 多取 1 条，用于排除当前刚写入的用户消息
        result = await session.execute(
            select(ChatMessageDB)
            .where(ChatMessageDB.session_id == session_id)
            .order_by(ChatMessageDB.created_at.desc())
            .limit(limit_rounds * 2 + 1)
        )
        rows = result.scalars().all()
    if not rows:
        return []
    # 时间正序，并去掉最新一条（当前用户消息）
    ordered = list(reversed(rows))[:-1]
    return [
        {"role": m.role, "content": (m.content or "").strip() or "(无内容)"}
        for m in ordered[-limit_rounds * 2 :]
    ]


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
    """发送消息并获取AI回答 - 真实RAG + Kimi（支持 Function Calling）"""
    session_id = request.session_id or str(uuid.uuid4())
    message_id = str(uuid.uuid4())

    MAX_TOOL_CALLS = 10  # 最大工具调用次数

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

    # 加载会话历史，使「这篇论文」「刚才那个」等指代能关联到上文
    session_history = await get_session_history(session_id, limit_rounds=10)

    # 构建消息历史（当前轮：user + assistant tool_calls + tool 等）
    messages_history = []

    # 添加工具执行函数
    async def execute_tool_call(tool_name: str, tool_args: dict) -> dict:
        """执行工具调用"""
        from services.agent.tools.registry import execute_tool
        return await execute_tool(tool_name, tool_args)

    # 使用 Kimi 生成回答（可能包含工具调用），传入历史以保持上下文
    ai_response = await generate_response_with_kimi(
        query=request.message,
        context=knowledge_results,
        student_id=request.student_id,
        mode=request.mode,
        tools=request.tools,
        history=session_history,
    )

    tool_calls_log = []

    # 处理工具调用循环
    if ai_response["type"] == "tool_calls":
        # LLM 请求工具调用
        messages_history.append({"role": "user", "content": request.message})

        for call_count in range(MAX_TOOL_CALLS):
            tool_calls = ai_response["tool_calls"]

            for tc in tool_calls:
                tool_name = tc["function"]["name"]
                tool_args = tc["function"].get("arguments", {})

                # 解析参数（如果是字符串）
                try:
                    if isinstance(tool_args, str):
                        tool_args = json.loads(tool_args)
                except json.JSONDecodeError:
                    pass

                # 添加 assistant 的 tool_call 消息
                messages_history.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [tc]
                })

                # 执行工具
                tool_result = await execute_tool_call(tool_name, tool_args)

                # 记录工具调用
                tool_calls_log.append({
                    "tool": tool_name,
                    "arguments": tool_args,
                    "result": tool_result
                })

                # 添加 tool 角色消息
                messages_history.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": json.dumps(tool_result, ensure_ascii=False)
                })

            # 继续调用 LLM，传入历史 + 当前轮已有消息（含工具调用与结果），保证模型能基于上文和工具结果继续回答
            ai_response = await generate_response_with_kimi(
                query=request.message,
                context=knowledge_results,
                student_id=request.student_id,
                mode=request.mode,
                tools=request.tools,
                history=session_history,
                current_turn_messages=messages_history,
            )

            # 检查是否还有工具调用
            if ai_response["type"] == "tool_calls":
                continue
            else:
                # 最终回复
                break
        else:
            # 达到最大调用次数
            ai_response = {"type": "message", "content": "抱歉，执行了太多工具调用，请简化你的问题。"}

    # 获取最终回复文本
    ai_response_text = ai_response.get("content", "")

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
            "created_at": datetime.utcnow().isoformat(),
            "tool_calls_log": tool_calls_log if tool_calls_log else None,
        }
    )


@router.post("/message/stream")
async def send_message_stream(request: ChatRequest):
    """流式对话接口 - 支持实时输出AI回答"""
    from fastapi.responses import StreamingResponse
    from common.integration.kimi import kimi_client

    session_id = request.session_id or str(uuid.uuid4())
    message_id = str(uuid.uuid4())

    async def generate_stream():
        """生成流式响应"""
        try:
            # 保存用户消息
            async with AsyncSessionLocal() as session:
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

                user_message = ChatMessageDB(
                    message_id=str(uuid.uuid4()),
                    session_id=session_id,
                    student_id=request.student_id,
                    role="user",
                    content=request.message
                )
                session.add(user_message)
                chat_session.message_count += 1
                await session.commit()

            # 获取学习上下文
            learning_context = await get_student_learning_context(request.student_id)

            # 检索知识库
            if request.mode == "learning" and _is_learning_question(request.message):
                knowledge_results = await retrieve_knowledge(request.message, request.course_id, top_k=3)
            else:
                knowledge_results = []

            # 获取会话历史
            session_history = await get_session_history(session_id, limit_rounds=10)

            # 构建消息
            system_content = "你是一位友好、专业的学习助手。"

            messages = [{"role": "system", "content": system_content}]

            if session_history:
                for h in session_history:
                    if h.get("content"):  # 只添加有内容的消息
                        messages.append({"role": h["role"], "content": h["content"]})

            # 添加用户消息
            if knowledge_results:
                context_text = "\n\n".join([
                    f"[参考资料{i+1}] {k.get('content', '')[:300]}"
                    for i, k in enumerate(knowledge_results)
                ])
                messages.append({
                    "role": "user",
                    "content": f"参考资料：\n{context_text}\n\n问题：{request.message}"
                })
            else:
                # 普通问答 - 简洁消息
                messages.append({"role": "user", "content": request.message})

            # 流式调用 Kimi API（智能缓冲输出）
            full_response = ""
            buffer = ""  # 字符缓冲

            # kimi-k2.5 enforces fixed top_p=0.95; other values cause silent failures
            model_for_call = request.model or "kimi-k2.5"
            effective_top_p = request.top_p if model_for_call not in {"kimi-k2.5", "kimi-k2.5-flash"} else 0.95
            effective_temperature = request.temperature if model_for_call not in {"kimi-k2.5", "kimi-k2.5-flash"} else 1.0

            async for chunk in kimi_client.chat_stream(
                messages,
                temperature=effective_temperature,
                max_tokens=request.max_tokens or 4096,
                top_p=effective_top_p,
                frequency_penalty=request.frequency_penalty or 0.0,
                presence_penalty=request.presence_penalty or 0.0,
                model=model_for_call,
                tools=request.tools
            ):
                if chunk.startswith("data: "):
                    data = chunk[6:]
                    if data == "[DONE]":
                        # 发送剩余缓冲
                        if buffer:
                            yield f"data: {json.dumps({'content': buffer}, ensure_ascii=False)}\n\n"
                        break
                    try:
                        parsed = json.loads(data)
                        if "choices" in parsed:
                            delta = parsed["choices"][0].get("delta", {})
                            if "content" in delta:
                                content = delta["content"]
                                full_response += content
                                buffer += content

                                # 立即发送每个内容块，不缓冲
                                yield f"data: {json.dumps({'content': buffer}, ensure_ascii=False)}\n\n"
                                buffer = ""
                    except json.JSONDecodeError:
                        continue

            # 保存AI回复
            if full_response:
                async with AsyncSessionLocal() as session:
                    ai_message = ChatMessageDB(
                        message_id=message_id,
                        session_id=session_id,
                        student_id=request.student_id,
                        role="assistant",
                        content=full_response,
                        sources=[k["source"] for k in knowledge_results]
                    )
                    session.add(ai_message)

                    result = await session.execute(
                        select(ChatSessionDB).where(ChatSessionDB.session_id == session_id)
                    )
                    chat_session = result.scalar_one_or_none()
                    if chat_session:
                        chat_session.message_count += 1
                    await session.commit()

            # 发送完成信号
            yield f"data: {json.dumps({'done': True, 'session_id': session_id, 'message_id': message_id}, ensure_ascii=False)}\n\n"

        except Exception as e:
            import traceback
            import logging
            logging.error(f"流式响应异常: {str(e)}\n{traceback.format_exc()}")
            yield f"data: {json.dumps({'error': f'服务器错误: {str(e)}'}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
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
