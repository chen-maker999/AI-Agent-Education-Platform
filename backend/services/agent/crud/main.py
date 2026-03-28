"""Agent CRUD + Chat 接口"""
import json
import httpx
import asyncio
from uuid import uuid4
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from common.models.response import ResponseModel
from common.core.config import settings

# 导入工具注册表
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from services.agent.tools.registry import get_tools_for_agent, execute_tool

router = APIRouter(prefix="/agent", tags=["Agent"])

AGENT_DATA_DIR = Path(__file__).resolve().parent / "data"
AGENT_DATA_DIR.mkdir(parents=True, exist_ok=True)
AGENTS_FILE = AGENT_DATA_DIR / "agents.json"

# 最大工具调用次数，防止无限循环
MAX_TOOL_CALLS = 10

# Moonshot：仅 kimi-k2.5 / kimi-k2.5-flash 支持 image_url；勿用 env 默认的 turbo-preview 调多模态
KIMI_VISION_MODELS = frozenset({"kimi-k2.5", "kimi-k2.5-flash"})


async def _download_url_to_knowledge(url: str, filename: str, course_id: str) -> dict:
    """内部下载函数，直接处理 URL 并保存到知识库"""
    from services.knowledge.rag.main import process_file_upload

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }

    try:
        async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()

            raw_content = response.content
            content_type = response.headers.get("content-type", "").lower()

            # PDF 文件
            if "pdf" in content_type or url.lower().endswith(".pdf"):
                full_filename = f"{filename}.pdf"
                result = await process_file_upload(raw_content, full_filename, course_id)
                return {
                    "success": True,
                    "type": "pdf",
                    "filename": full_filename,
                    "doc_count": result.get("total_chunks", 1),
                    "size": len(raw_content),
                }

            # HTML 网页
            elif "text/html" in content_type:
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(raw_content, 'html.parser')
                    for script in soup(["script", "style"]):
                        script.decompose()
                    text = soup.get_text(separator="\n", strip=True)
                    lines = [line for line in text.splitlines() if line.strip()]
                    text = "\n".join(lines)
                except ImportError:
                    text = raw_content.decode("utf-8", errors="replace")

                full_filename = f"{filename}.txt"
                result = await process_file_upload(text.encode("utf-8"), full_filename, course_id)
                return {
                    "success": True,
                    "type": "webpage",
                    "filename": full_filename,
                    "doc_count": result.get("total_chunks", 1),
                    "size": len(raw_content),
                }

            # 其他类型，保存原始内容
            else:
                full_filename = f"{filename}.bin"
                result = await process_file_upload(raw_content, full_filename, course_id)
                return {
                    "success": True,
                    "type": "binary",
                    "filename": full_filename,
                    "doc_count": result.get("total_chunks", 1),
                    "size": len(raw_content),
                }

    except Exception as e:
        return {"success": False, "error": str(e)}


def _load_agents() -> List[dict]:
    if not AGENTS_FILE.exists():
        return []
    try:
        with open(AGENTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_agents(agents: List[dict]):
    with open(AGENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(agents, f, ensure_ascii=False, indent=2)


# --- Pydantic 模型 ---
class AgentCreate(BaseModel):
    name: str = Field(..., description="智能体名称")
    prompt: str = Field("", description="提示词")
    callable_by_others: bool = Field(False)
    english_id: str = Field("")
    when_to_call: str = Field("")
    enabled_tools: List[str] = Field(default_factory=list)
    avatar: Optional[str] = None


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    prompt: Optional[str] = None
    callable_by_others: Optional[bool] = None
    english_id: Optional[str] = None
    when_to_call: Optional[str] = None
    enabled_tools: Optional[List[str]] = None
    avatar: Optional[str] = None


class ChatRequest(BaseModel):
    agent_id: str
    message: str
    student_id: str = "default"
    session_id: Optional[str] = None
    # 模型参数
    model: Optional[str] = "kimi-k2.5"
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.9
    max_tokens: Optional[int] = 4096
    frequency_penalty: Optional[float] = 0.0
    presence_penalty: Optional[float] = 0.0
    # 工具权限
    tools: Optional[List[Dict[str, Any]]] = None
    # 多模态支持：图片/文档 base64 数据
    files: Optional[List[Dict[str, str]]] = None  # [{type: "image/jpeg", data: "base64..."}]


# --- CRUD ---

@router.get("", response_model=ResponseModel)
async def list_agents():
    agents = _load_agents()
    return ResponseModel(code=200, message="success", data={"agents": agents})


@router.get("/{agent_id}", response_model=ResponseModel)
async def get_agent(agent_id: str):
    agents = _load_agents()
    for a in agents:
        if a["id"] == agent_id:
            return ResponseModel(code=200, message="success", data=a)
    return ResponseModel(code=404, message="智能体不存在")


@router.post("", response_model=ResponseModel)
async def create_agent(data: AgentCreate):
    agents = _load_agents()
    if any(a["name"] == data.name for a in agents):
        return ResponseModel(code=400, message="智能体名称已存在")
    agent = {
        "id": str(uuid4()),
        "name": data.name,
        "prompt": data.prompt,
        "callable_by_others": data.callable_by_others,
        "english_id": data.english_id,
        "when_to_call": data.when_to_call,
        "enabled_tools": data.enabled_tools,
        "avatar": data.avatar,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    agents.append(agent)
    _save_agents(agents)
    return ResponseModel(code=201, message="success", data=agent)


@router.put("/{agent_id}", response_model=ResponseModel)
async def update_agent(agent_id: str, data: AgentUpdate):
    agents = _load_agents()
    for i, a in enumerate(agents):
        if a["id"] == agent_id:
            update_data = data.model_dump(exclude_unset=True)
            agents[i].update(update_data)
            agents[i]["updated_at"] = datetime.utcnow().isoformat()
            _save_agents(agents)
            return ResponseModel(code=200, message="success", data=agents[i])
    return ResponseModel(code=404, message="智能体不存在")


@router.delete("/{agent_id}", response_model=ResponseModel)
async def delete_agent(agent_id: str):
    agents = _load_agents()
    new_agents = [a for a in agents if a["id"] != agent_id]
    if len(new_agents) == len(agents):
        return ResponseModel(code=404, message="智能体不存在")
    _save_agents(new_agents)
    return ResponseModel(code=200, message="删除成功")


# --- Chat ---
SESSIONS_DIR = AGENT_DATA_DIR / "sessions"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


def _load_session(session_id: str) -> List[dict]:
    f = SESSIONS_DIR / f"{session_id}.json"
    if f.exists():
        try:
            with open(f, "r", encoding="utf-8") as fp:
                return json.load(fp)
        except Exception:
            pass
    return []


def _save_session(session_id: str, messages: List[dict]):
    f = SESSIONS_DIR / f"{session_id}.json"
    with open(f, "w", encoding="utf-8") as fp:
        json.dump(messages, fp, ensure_ascii=False, indent=2)


async def _call_llm(
    messages: List[dict],
    tools: Optional[List[dict]] = None
) -> str:
    """调用后端 /chat/message 接口获取 LLM 回复（支持 Function Calling）"""
    try:
        # 构造 chat message 格式
        text = messages[-1]["content"] if messages else ""
        payload = {
            "message": text,
            "mode": "general",
            "student_id": "agent",
            "session_id": None,
            "course_id": None,
        }

        # 如果有工具定义，也传给后端
        if tools:
            payload["tools"] = tools

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"http://localhost:8000{settings.API_PREFIX}/chat/message",
                json=payload,
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 200 and data.get("data", {}).get("response"):
                    return data["data"]["response"]
    except Exception:
        pass
    # 降级：返回简单回复
    return f"已收到你的消息。当前智能体正在处理中，请稍候。"


async def _call_llm_with_tools(
    messages: List[dict],
    tools: List[dict],
    model: str = "kimi-k2.5",
    temperature: float = 1.0,  # kimi-k2.5 模型只接受 temperature=1
    max_tokens: int = 4096,
    top_p: float = 1.0,
    frequency_penalty: float = 0.0,
    presence_penalty: float = 0.0
) -> dict:
    """
    调用 Kimi API 获取 LLM 回复（支持 Function Calling）

    Returns:
        {
            "type": "message" | "tool_calls",
            "content": str,  # 如果是普通消息
            "tool_calls": [...] # 如果是工具调用
        }
    """
    from common.integration.kimi import kimi_client

    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"[_call_llm_with_tools] model={model}, msgs={len(messages)}, tools={len(tools)}")
    for i, m in enumerate(messages):
        c = m.get("content", "")
        role = m.get("role", "?")
        if isinstance(c, list):
            blocks = [{"type": b.get("type") for b in c}]
            logger.info(f"  msg[{i}] role={role} blocks={blocks}")
        else:
            logger.info(f"  msg[{i}] role={role} content={str(c)[:100]}")

    try:
        result = await kimi_client.chat(
            messages=messages,
            tools=tools,
            model=model,
            temperature=1.0,  # kimi-k2.5 模型只接受 temperature=1
            max_tokens=max_tokens,
            top_p=1.0,  # kimi-k2.5 模型需要使用 1.0
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty
        )

        if "error" in result:
            detail = result.get("detail") or ""
            err_text = f"抱歉，调用 AI 服务时出错：{result['error']}"
            if detail:
                err_text = err_text + " " + detail[:800]
            return {
                "type": "message",
                "content": err_text
            }

        choices = result.get("choices", [])
        if not choices:
            return {"type": "message", "content": "抱歉，没有收到 AI 的回复。"}

        message = choices[0].get("message", {})

        # 检查是否有 tool_calls
        if "tool_calls" in message and message["tool_calls"]:
            return {
                "type": "tool_calls",
                "tool_calls": message["tool_calls"],
                "_raw_message": message  # 保存原始消息，包含 reasoning_content
            }

        # 普通文本回复
        content = message.get("content", "")
        return {"type": "message", "content": content, "_raw_message": message}

    except Exception as e:
        return {"type": "message", "content": f"抱歉，调用 AI 服务时出错：{str(e)}"}


@router.post("/chat", response_model=ResponseModel)
async def agent_chat(data: ChatRequest):
    """与指定智能体对话（支持 Function Calling）"""
    agents = _load_agents()
    agent = next((a for a in agents if a["id"] == data.agent_id), None)
    if not agent:
        return ResponseModel(code=404, message="智能体不存在")

    session_id = data.session_id or str(uuid4())
    history = _load_session(session_id)

    # 构建用户消息（支持多模态）
    # 所有文件都上传到 Kimi 获取 file_id，然后用 file 格式引用
    user_msg = {"role": "user", "content": data.message}
    
    # 处理文件上传
    file_messages = []  # 存储多模态消息块
    file_text_contents = []  # 存储文档抽取的文本内容
    
    if data.files:
        from common.integration.kimi import kimi_client
        import logging
        logger = logging.getLogger(__name__)
        
        for f in data.files:
            file_type = f.get("type", "application/octet-stream")
            file_data = f.get("data", "")
            data_len = len(file_data)
            
            logger.info(f"正在处理文件: type={file_type}, data_len={data_len}")
            
            # 空数据检查
            if not file_data:
                logger.warning("文件数据为空，跳过")
                continue
            
            # 图片文件：使用 image_url 格式（兼容 kimi-k2.5）
            if file_type.startswith("image/"):
                # 构建 image_url 格式（将 base64 转为 data URL）
                data_url = f"data:{file_type};base64,{file_data}"
                file_messages.append({
                    "type": "image_url",
                    "image_url": {
                        "url": data_url
                    }
                })
                logger.info(f"图片已转换为 image_url 格式: type={file_type}, size={data_len}")
            elif file_type.startswith("video/"):
                # 视频暂不支持，使用 text_only 模式提示
                logger.warning(f"视频文件暂不支持: type={file_type}")
            else:
                # 文档使用 file-extract，获取文本内容作为 system 消息
                # 先上传获取 file_id
                file_id = await kimi_client.upload_file(file_data, file_type, "file-extract")
                if file_id:
                    content = await kimi_client.get_file_content(file_id)
                    if content:
                        file_text_contents.append(content)
                        logger.info(f"文档内容获取成功: content_len={len(content)}")
                    else:
                        logger.warning(f"文档内容获取失败，但文件已上传: file_id={file_id}")
                else:
                    logger.warning(f"文档上传失败: type={file_type}")
    
    # 用户消息入历史（存储文本形式）
    history.append({
        "role": "user",
        "content": data.message,
        "time": datetime.utcnow().isoformat(),
    })

    # 拼接 system prompt
    system_prompt = agent.get("prompt", "") or (
        f"你是一个名为「{agent['name']}」的AI助手。请根据用户的问题给出专业、准确、有帮助的回答。"
    )

    # 获取 Agent 启用的工具
    enabled_tools = agent.get("enabled_tools", [])
    tools = get_tools_for_agent(enabled_tools)

    # 构建发给 LLM 的消息
    # 【关键】将工具使用规则放在 system prompt 最前面，确保模型优先遵循
    if tools:
        tool_names = [t["function"]["name"] for t in tools]
        core_rules = ""
        core_rules += "\n【重要】你是一个智能助手，可以通过调用工具来完成任务。"

        # 文件读写工具规则（只针对上传的文件）
        if 'reading' in tool_names or 'editing' in tool_names:
            core_rules += "\n【文件操作】reading 和 editing 工具只能访问用户在当前对话中上传的文件，"
            core_rules += "不能访问工作区、项目目录或其他系统文件。当用户提到「我上传的文件」「刚才的文件」时才使用文件工具。"

        # download_to_knowledge 强制规则
        if 'download_to_knowledge' in tool_names:
            core_rules += "\n【最高优先级】当用户要求保存资料到知识库时："
            core_rules += "1) 立即调用 download_to_knowledge 工具；2) course_id='default'；3) 禁止询问任何路径问题，直接执行！"

        # 添加知识库检索工具提示
        if 'knowledge_search' in tool_names:
            core_rules += "\n【知识库检索】当用户询问需要查找资料、解释概念、回答与已上传文档相关的问题时，可以调用 knowledge_search 工具搜索知识库。"

        # 联网搜索规则
        if 'web_search' in tool_names:
            core_rules += "\n【联网搜索】当用户询问最新信息、新闻、实时数据时，应该调用 web_search 工具。"

        # 终端命令规则
        if 'terminal' in tool_names:
            core_rules += "\n【终端命令】当用户要求运行代码、安装依赖、执行命令时，可以调用 terminal 工具。注意：只执行安全的命令。"

        # 添加工具列表
        core_rules += f"\n\n可用工具：{', '.join(tool_names)}"

        # 将核心规则放在 system prompt 最前面
        llm_messages = [{"role": "system", "content": core_rules + "\n\n" + system_prompt}]
    else:
        llm_messages = [{"role": "system", "content": system_prompt}]
    
    # 添加上传文档的内容（作为 system 消息）
    if file_text_contents:
        for fc in file_text_contents:
            truncated_content = fc[:10000]
            if len(fc) > 10000:
                truncated_content += f"\n\n[文件内容已截断，原长度 {len(fc)} 字符]"
            llm_messages.append({
                "role": "system",
                "content": f"【用户上传的文档内容】\n{truncated_content}"
            })

    # 添加历史消息（仅文本形式）
    for msg in history[:-1]:  # 不包含当前用户消息
        llm_messages.append({"role": msg["role"], "content": msg["content"]})
    
    # 构建用户消息（支持多模态）
    if file_messages:
        user_content = []
        for block in file_messages:
            user_content.append(block)
        user_content.append({
            "type": "text",
            "text": data.message
        })
        llm_messages.append({"role": "user", "content": user_content})
    else:
        llm_messages.append({"role": "user", "content": data.message})

    # 定义 has_tools
    has_tools = len(tools) > 0
    tool_names_list = [t["function"]["name"] for t in tools] if has_tools else []
    tool_calls_log = []  # 定义在前面，供下载检测逻辑使用
    
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"[Agent Chat] has_tools={has_tools}, tool_names={tool_names_list}")
    logger.info(f"[Agent Chat] 多模态消息: user_msg type={'list' if isinstance(user_msg.get('content'), list) else 'str'}")

    requested_model = data.model or "kimi-k2.5"
    llm_model = requested_model
    if file_messages:
        if llm_model not in KIMI_VISION_MODELS:
            llm_model = "kimi-k2.5"

    # 【关键修复】检测用户消息中的"下载到知识库"意图，自动执行工具
    if has_tools and 'download_to_knowledge' in tool_names_list:
            # 尝试从消息中提取 URL
            import re
            url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
            urls = re.findall(url_pattern, data.message)

            if urls:
                url = urls[0]
                # 从 URL 提取文件名
                filename = url.split('/')[-1].split('?')[0] or "document"
                if not any(ext in filename.lower() for ext in ['.pdf', '.doc', '.txt', '.html']):
                    filename += ".pdf"

                # 直接调用下载逻辑
                tool_result = await _download_url_to_knowledge(url, filename.rsplit('.', 1)[0] if '.' in filename else filename, 'default')

                tool_calls_log.append({
                    "tool": "download_to_knowledge",
                    "arguments": {'url': url, 'filename': filename, 'course_id': 'default'},
                    "result": tool_result
                })

                # 直接返回结果
                if tool_result.get('success'):
                    response_text = f"已将「{filename}」保存到知识库。"
                else:
                    response_text = f"保存失败：{tool_result.get('error', '未知错误')}"

                history.append({
                    "role": "assistant",
                    "content": response_text,
                    "time": datetime.utcnow().isoformat(),
                })
                _save_session(session_id, history)

                return ResponseModel(
                    code=200,
                    message="success",
                    data={
                        "response": response_text,
                        "session_id": session_id,
                        "agent_name": agent["name"],
                        "agent_id": agent["id"],
                        "history": history,
                        "tool_calls_log": tool_calls_log,
                    },
                )

    # 正常流程：工具调用循环
    last_llm_message = None  # 保存最后一次 LLM 返回的消息（用于 reasoning_content）
    if has_tools:
        for call_count in range(MAX_TOOL_CALLS):
            # 调用 LLM（带工具）
            llm_response = await _call_llm_with_tools(
                llm_messages, 
                tools,
                model=llm_model,
                temperature=1.0,  # kimi-k2.5 模型只接受 temperature=1
                max_tokens=data.max_tokens or 4096,
                top_p=1.0,  # kimi-k2.5 模型需要使用 1.0
                frequency_penalty=data.frequency_penalty or 0.0,
                presence_penalty=data.presence_penalty or 0.0
            )

            if llm_response["type"] == "message":
                # 普通文本回复
                response_text = llm_response["content"]
                break

            elif llm_response["type"] == "tool_calls":
                # 收到工具调用请求
                tool_calls = llm_response["tool_calls"]
                last_llm_message = llm_response.get("_raw_message")  # 获取原始消息

                for tc in tool_calls:
                    tool_name = tc["function"]["name"]
                    tool_args = tc["function"]["arguments"]

                    # 解析参数
                    try:
                        if isinstance(tool_args, str):
                            tool_args = json.loads(tool_args)
                    except json.JSONDecodeError:
                        tool_args = {}

                    # 添加 assistant 的 tool_call 消息
                    # kimi-k2.5 模型需要包含 reasoning_content
                    tool_call_msg = {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [tc]
                    }
                    # 如果消息中有 reasoning_content，需要传递
                    if last_llm_message and last_llm_message.get("reasoning_content"):
                        tool_call_msg["reasoning_content"] = last_llm_message.get("reasoning_content")
                    llm_messages.append(tool_call_msg)

                    # 构建后端地址
                    backend_url = f"http://{settings.HOST or '127.0.0.1'}:{settings.PORT or 8000}"

                    # 执行工具
                    tool_result = await execute_tool(tool_name, tool_args, base_url=backend_url)

                    # 记录工具调用
                    tool_calls_log.append({
                        "tool": tool_name,
                        "arguments": tool_args,
                        "result": tool_result
                    })

                    # 添加 tool 角色消息
                    llm_messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": json.dumps(tool_result, ensure_ascii=False)
                    })

                # 继续循环，检查是否还有工具调用
                continue

        else:
            # 达到最大调用次数
            response_text = "抱歉，执行了太多工具调用，请简化你的问题。"
    else:
        last_user = llm_messages[-1] if llm_messages else None
        if last_user and last_user.get("role") == "user" and isinstance(last_user.get("content"), list):
            from common.integration.kimi import kimi_client
            result = await kimi_client.chat(
                messages=llm_messages,
                model=llm_model,
                temperature=1.0,
                max_tokens=data.max_tokens or 4096,
                top_p=1.0,
                frequency_penalty=data.frequency_penalty or 0.0,
                presence_penalty=data.presence_penalty or 0.0,
            )
            if "error" in result:
                detail = result.get("detail") or ""
                response_text = f"抱歉，调用 AI 服务时出错：{result['error']}"
                if detail:
                    response_text = response_text + " " + detail[:800]
            else:
                choices = result.get("choices", [])
                if choices:
                    response_text = (choices[0].get("message") or {}).get("content", "") or "（无回复）"
                else:
                    response_text = "抱歉，没有收到 AI 的回复。"
        else:
            response_text = await _call_llm(llm_messages)

    # AI 回复入历史
    history.append({
        "role": "assistant",
        "content": response_text,
        "time": datetime.utcnow().isoformat(),
    })
    _save_session(session_id, history)

    return ResponseModel(
        code=200,
        message="success",
        data={
            "response": response_text,
            "session_id": session_id,
            "agent_name": agent["name"],
            "agent_id": agent["id"],
            "history": history,
            "tool_calls_log": tool_calls_log if tool_calls_log else None,
        },
    )
