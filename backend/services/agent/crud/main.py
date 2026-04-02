"""Agent CRUD + Chat 接口 - 增强版（集成 Agent 类型、内存、钩子、子代理）"""
import json
import hashlib
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
from services.agent.tools.registry import get_tools_for_agent, execute_tool, is_tool_allowed

# 导入增强模块
from services.agent.prompts import (
    build_agent_system_prompt,
    build_tool_rules,
    build_memory_prompt,
    build_context_prompt,
    AGENT_TYPE_SYSTEM_PROMPTS,
    get_when_to_use_prompt
)
from services.agent.memory import add_session_memory, get_session_memory, agent_memory
from services.agent.hooks import hook_manager, filter_message, process_response
from services.agent.subagent import task_manager, TaskType
from services.agent.types import AgentType, AgentDefinition

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
    agent_type: str = Field("general", description="Agent类型: general, explorer, planner, verifier, tutor, grader, custom")
    callable_by_others: bool = Field(False)
    english_id: str = Field("")
    when_to_call: str = Field("")
    when_not_to_call: str = Field("", description="何时不使用此Agent")
    enabled_tools: List[str] = Field(default_factory=list)
    avatar: Optional[str] = None
    color: Optional[str] = Field(None, description="UI颜色")
    model: Optional[str] = Field(None, description="指定模型")
    memory_enabled: bool = Field(True, description="是否启用记忆")
    max_tool_calls: int = Field(10, ge=1, le=50, description="最大工具调用次数")
    max_turns: int = Field(20, ge=1, le=100, description="最大对话轮次")


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    prompt: Optional[str] = None
    agent_type: Optional[str] = None
    callable_by_others: Optional[bool] = None
    english_id: Optional[str] = None
    when_to_call: Optional[str] = None
    when_not_to_call: Optional[str] = None
    enabled_tools: Optional[List[str]] = None
    avatar: Optional[str] = None
    color: Optional[str] = None
    model: Optional[str] = None
    memory_enabled: Optional[bool] = None
    max_tool_calls: Optional[int] = None
    max_turns: Optional[int] = None


def _extract_content(message: dict) -> str:
    """从 Kimi 回复的 message 中提取文本内容。

    kimi-k2.5 可能把内容放在 content 或 reasoning_content 字段中：
    - reasoning_content：推理过程（Kimi-k2.5 主要在此返回内容）
    - content：最终回复（有时为空）
    两者都存在时优先取 content，若为空则取 reasoning_content。
    """
    content = message.get("content", "")
    if content and content.strip():
        return content
    reasoning = message.get("reasoning_content", "")
    if reasoning and reasoning.strip():
        return reasoning
    return content or ""


class ChatRequest(BaseModel):
    agent_id: Optional[str] = Field(None, description="可选，不传则自动使用最新 Agent")
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
    # 增强功能
    use_memory: bool = Field(True, description="是否使用记忆")
    enable_hooks: bool = Field(True, description="是否启用钩子")
    context: Optional[Dict[str, Any]] = Field(None, description="额外上下文")
    # Agent 配置（从前端配置中心传入）
    agent_type: Optional[str] = Field("tutor", description="Agent 类型，决定系统提示词模板")
    personality: Optional[str] = Field("balanced", description="性格倾向")
    custom_prompt: Optional[str] = Field("", description="自定义提示词")


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
async def create_or_update_agent(data: AgentCreate):
    """创建或更新智能体（同名则更新）"""
    agents = _load_agents()
    
    # 查找同名 Agent
    existing_idx = None
    for i, a in enumerate(agents):
        if a["name"] == data.name:
            existing_idx = i
            break
    
    now = datetime.utcnow().isoformat()
    
    if existing_idx is not None:
        # 更新已存在的 Agent
        update_data = data.model_dump(exclude_unset=True)
        agents[existing_idx].update(update_data)
        agents[existing_idx]["updated_at"] = now
        _save_agents(agents)
        return ResponseModel(code=200, message="智能体已更新", data=agents[existing_idx])
    else:
        # 创建新 Agent
        agent = {
            "id": str(uuid4()),
            "name": data.name,
            "prompt": data.prompt,
            "agent_type": data.agent_type,
            "callable_by_others": data.callable_by_others,
            "english_id": data.english_id,
            "when_to_call": data.when_to_call,
            "when_not_to_call": data.when_not_to_call,
            "enabled_tools": data.enabled_tools,
            "avatar": data.avatar,
            "color": data.color,
            "model": data.model,
            "memory_enabled": data.memory_enabled,
            "max_tool_calls": data.max_tool_calls,
            "max_turns": data.max_turns,
            "created_at": now,
            "updated_at": now,
        }
        agents.append(agent)
        _save_agents(agents)
        return ResponseModel(code=201, message="智能体创建成功", data=agent)


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


# --- Agent 类型相关 API ---

@router.get("/types/list", response_model=ResponseModel)
async def list_agent_types():
    """列出所有支持的 Agent 类型"""
    types_info = {
        "general": {
            "id": "general",
            "name": "通用代理",
            "description": "处理各种任务的通用智能体",
            "recommended_tools": ["reading", "editing", "terminal", "tavily_search", "knowledge_search"]
        },
        "explorer": {
            "id": "explorer",
            "name": "探索代理",
            "description": "专门进行代码搜索和分析（只读模式）",
            "recommended_tools": ["reading", "tavily_search", "knowledge_search"],
            "disallowed_tools": ["editing", "terminal"]
        },
        "planner": {
            "id": "planner",
            "name": "计划代理",
            "description": "专门进行需求分析和架构设计",
            "recommended_tools": ["reading", "tavily_search", "knowledge_search"],
            "disallowed_tools": ["editing", "terminal"]
        },
        "verifier": {
            "id": "verifier",
            "name": "验证代理",
            "description": "专门验证实现是否符合需求",
            "recommended_tools": ["reading", "terminal", "knowledge_search"]
        },
        "tutor": {
            "id": "tutor",
            "name": "辅导代理",
            "description": "专门帮助学生学习",
            "recommended_tools": ["tavily_search", "knowledge_search", "preview"],
            "disallowed_tools": ["editing", "terminal"]
        },
        "grader": {
            "id": "grader",
            "name": "批改代理",
            "description": "专门批改作业和评分",
            "recommended_tools": ["reading", "editing", "knowledge_search"],
            "disallowed_tools": ["terminal"]
        },
        "custom": {
            "id": "custom",
            "name": "自定义代理",
            "description": "用户自定义的智能体",
            "recommended_tools": ["reading", "tavily_search", "knowledge_search"],
            "disallowed_tools": ["terminal"]
        }
    }
    return ResponseModel(code=200, message="success", data={"types": types_info})


# --- 工具相关 API ---

@router.get("/tools/available", response_model=ResponseModel)
async def list_available_tools():
    """列出所有可用的工具"""
    from services.agent.tools.registry import get_tools_metadata
    return ResponseModel(code=200, message="success", data={"tools": get_tools_metadata()})


@router.get("/tools/permissions/{agent_type}", response_model=ResponseModel)
async def get_tool_permissions(agent_type: str):
    """获取指定 Agent 类型的工具权限"""
    from services.agent.tools.registry import is_tool_allowed, ALL_AGENT_DISALLOWED_TOOLS, AGENT_TYPE_DISALLOWED_TOOLS
    
    all_tools = ["reading", "editing", "terminal", "preview", "tavily_search", "download_to_knowledge", "knowledge_search"]
    permissions = {}
    
    for tool in all_tools:
        allowed = is_tool_allowed(tool, agent_type)
        permissions[tool] = {
            "allowed": allowed,
            "reason": "禁止使用" if not allowed else "允许使用"
        }
    
    return ResponseModel(code=200, message="success", data={
        "agent_type": agent_type,
        "permissions": permissions,
        "default_disallowed": list(ALL_AGENT_DISALLOWED_TOOLS),
        "type_disallowed": list(AGENT_TYPE_DISALLOWED_TOOLS.get(agent_type, set()))
    })


# --- 记忆相关 API ---

@router.get("/memory/{session_id}", response_model=ResponseModel)
async def get_session_memories(session_id: str, limit: int = 10):
    """获取会话记忆"""
    from services.agent.memory import get_session_memory
    memory = get_session_memory(session_id, limit)
    return ResponseModel(code=200, message="success", data={"session_id": session_id, "memory": memory})


@router.delete("/memory/{session_id}", response_model=ResponseModel)
async def clear_session_memory(session_id: str):
    """清除会话记忆"""
    from services.agent.memory import agent_memory, MemoryScope
    count = agent_memory.clear_session(session_id)
    return ResponseModel(code=200, message="success", data={"session_id": session_id, "cleared_count": count})


@router.post("/memory/{session_id}", response_model=ResponseModel)
async def add_memory(
    session_id: str,
    content: str,
    importance: float = 1.0,
    tags: str = ""
):
    """添加会话记忆"""
    from services.agent.memory import add_session_memory
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else None
    memory = add_session_memory(session_id, content, importance, tag_list)
    return ResponseModel(code=200, message="success", data=memory.to_dict())


# --- 钩子相关 API ---

@router.get("/hooks", response_model=ResponseModel)
async def list_hooks():
    """列出所有钩子"""
    from services.agent.hooks import list_available_hooks
    hooks = list_available_hooks()
    return ResponseModel(code=200, message="success", data={"hooks": hooks})


# --- 子代理相关 API ---

@router.get("/tasks", response_model=ResponseModel)
async def list_tasks(status: str = None):
    """列出任务"""
    from services.agent.subagent import TaskStatus
    tasks = task_manager.list_tasks(
        status=TaskStatus(status) if status else None
    )
    return ResponseModel(code=200, message="success", data={
        "tasks": [t.to_dict() for t in tasks]
    })


@router.get("/tasks/{task_id}", response_model=ResponseModel)
async def get_task_status(task_id: str):
    """获取任务状态"""
    task = task_manager.get_task(task_id)
    if not task:
        return ResponseModel(code=404, message="任务不存在")
    return ResponseModel(code=200, message="success", data=task.to_dict())


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
    tools: Optional[List[dict]] = None,
    model: str = "kimi-k2.5",
    max_tokens: int = 4096,
    temperature: float = 1.0,
    top_p: float = 1.0,
    frequency_penalty: float = 0.0,
    presence_penalty: float = 0.0
) -> str:
    """直接调用 Kimi API 获取 LLM 回复（支持多模态消息）。

    重要：messages 中的最后一条消息的 content 可能是 list（包含 image_url blocks），
    不能转成字符串，必须直接传给 kimi_client.chat()。
    """
    import logging
    logger = logging.getLogger(__name__)

    last_msg = messages[-1] if messages else None
    last_content = last_msg.get("content") if last_msg else None

    # 如果最后一条消息是多模态列表（包含图片/文件），直接调用 kimi_client.chat
    if isinstance(last_content, list):
        from common.integration.kimi import kimi_client as kc
        try:
            result = await kc.chat(
                messages=messages,
                tools=tools,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
            )
            if "error" in result:
                detail = result.get("detail") or ""
                logger.error(f"[_call_llm] Kimi API error: {result['error']} | {detail[:200]}")
                return f"抱歉，调用 AI 服务时出错：{result['error']}"
            choices = result.get("choices", [])
            if choices:
                message = choices[0].get("message") or {}
                content = _extract_content(message)
                return content if content else "（无回复）"
            return "（无回复）"
        except Exception as e:
            logger.error(f"[_call_llm] Exception: {e}")
            return f"已收到你的消息。当前智能体正在处理中，请稍候。"

    # 纯文本消息：兼容调用 /chat/message 接口（兜底）
    try:
        text = last_content or ""
        payload = {
            "message": text,
            "mode": "general",
            "student_id": "agent",
            "session_id": None,
            "course_id": None,
        }
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


async def _call_llm_stream_output(
    messages: List[dict],
    tools: List[dict],
    model: str = "kimi-k2.5",
    temperature: float = 1.0,
    max_tokens: int = 4096,
    top_p: float = 1.0,
    frequency_penalty: float = 0.0,
    presence_penalty: float = 0.0,
    yield_func=None
):
    """
    调用 Kimi API 并流式输出结果（支持 Function Calling）

    Args:
        yield_func: 用于输出数据的生成器函数
    """
    from common.integration.kimi import kimi_client
    import logging
    logger = logging.getLogger(__name__)

    tool_calls_log = []
    current_tool_call_msg = None

    while True:
        try:
            result = await kimi_client.chat(
                messages=messages,
                tools=tools,
                model=model,
                temperature=1.0,
                max_tokens=max_tokens,
                top_p=1.0,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty
            )

            if "error" in result:
                detail = result.get("detail") or ""
                err_text = f"抱歉，调用 AI 服务时出错：{result['error']}"
                if detail:
                    err_text = err_text + " " + detail[:800]
                if yield_func:
                    yield_func(err_text)
                return err_text, tool_calls_log

            choices = result.get("choices", [])
            if not choices:
                err_text = "抱歉，没有收到 AI 的回复。"
                if yield_func:
                    yield_func(err_text)
                return err_text, tool_calls_log

            message = choices[0].get("message", {})

            # 检查是否有 tool_calls
            if "tool_calls" in message and message["tool_calls"]:
                for tc in message["tool_calls"]:
                    tool_name = tc["function"]["name"]
                    tool_args = tc["function"].get("arguments", {})

                    try:
                        if isinstance(tool_args, str):
                            tool_args = json.loads(tool_args)
                    except json.JSONDecodeError:
                        tool_args = {}

                    # 添加 assistant 的 tool_call 消息
                    tool_call_msg = {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [tc]
                    }
                    if message.get("reasoning_content"):
                        tool_call_msg["reasoning_content"] = message.get("reasoning_content")
                    messages.append(tool_call_msg)

                    # 执行工具
                    backend_url = f"http://{settings.HOST or '127.0.0.1'}:{settings.PORT or 8000}"
                    tool_result = await execute_tool(tool_name, tool_args, base_url=backend_url)

                    tool_calls_log.append({
                        "tool": tool_name,
                        "arguments": tool_args,
                        "result": tool_result
                    })

                    # 添加 tool 角色消息
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": json.dumps(tool_result, ensure_ascii=False)
                    })

                # 继续循环，获取最终回复
                continue

            # 普通文本回复 - 流式输出
            content = message.get("content", "")
            if content and yield_func:
                # 逐字符/词输出，模拟打字效果
                for i in range(0, len(content), 3):
                    chunk = content[i:i+3]
                    yield_func(chunk)
                    await asyncio.sleep(0.005)  # 控制输出速度

            return content, tool_calls_log

        except Exception as e:
            err_text = f"抱歉，调用 AI 服务时出错：{str(e)}"
            if yield_func:
                yield_func(err_text)
            return err_text, tool_calls_log


@router.post("/chat", response_model=ResponseModel)
async def agent_chat(data: ChatRequest):
    """与最新智能体对话（自动使用最新创建的 Agent）"""
    agents = _load_agents()
    
    # 按 updated_at 排序，获取最新的 Agent
    if agents:
        agents.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        agent = agents[0]  # 使用最新的 Agent
    else:
        return ResponseModel(code=404, message="请先创建智能体")

    session_id = data.session_id or str(uuid4())
    history = _load_session(session_id)

    # 优先使用前端传入的配置，否则回退到 Agent 配置
    agent_type = data.agent_type or agent.get("agent_type", "tutor")
    memory_enabled = data.use_memory if data.use_memory is not None else agent.get("memory_enabled", True)
    custom_prompt = data.custom_prompt or agent.get("prompt", "")
    personality = data.personality or agent.get("personality", "balanced")

    # ========== 消息过滤（钩子前置处理） ==========
    if data.enable_hooks:
        hook_context = {
            "agent_id": agent["id"],
            "agent_type": agent_type,
            "session_id": session_id,
            "student_id": data.student_id
        }
        filtered_message = await filter_message(data.message, hook_context)
        if filtered_message != data.message:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"[Agent Chat] 消息经过钩子过滤: {len(data.message)} -> {len(filtered_message)}")

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
                        "url": data_url,
                        "detail": "high",
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

    # ========== 构建增强的 System Prompt ==========

    # 获取 Agent 启用的工具
    enabled_tools = agent.get("enabled_tools", [])

    # 构建完整的 system prompt（使用增强的 Prompt 系统）
    from services.agent.prompts import build_personality_prompt
    system_prompt = build_agent_system_prompt(
        agent_type=agent_type,
        custom_prompt=custom_prompt,
        enabled_tools=enabled_tools,
        personality=personality
    )

    # 多图：子代理无法接收 image_url，禁止误导模型去 delegate「看图」
    if file_messages and len(file_messages) > 1:
        system_prompt += (
            "\n\n【重要：用户上传了多张图片】请在本条回复中**依次**阅读每张 image_url 并分析；"
            "**不要**使用 delegate_task 处理图片（子代理看不到图片）。"
        )

    # 获取工具定义
    tools = get_tools_for_agent(enabled_tools, agent_type)
    has_tools = len(tools) > 0
    tool_names_list = [t["function"]["name"] for t in tools] if has_tools else []

    # 构建发给 LLM 的消息列表
    llm_messages = [{"role": "system", "content": system_prompt}]

    # ========== 添加记忆内容 ==========
    if memory_enabled and data.use_memory:
        # 获取会话记忆
        session_memory = get_session_memory(session_id, limit=5)
        if session_memory:
            memory_prompt = build_memory_prompt(session_memory, scope="session")
            llm_messages.append({"role": "system", "content": memory_prompt})

        # 获取 Agent 持久记忆
        agent_memory_content = get_session_memory(f"agent_{agent['id']}", limit=10)
        if agent_memory_content:
            agent_memory_prompt = build_memory_prompt(agent_memory_content, scope="agent")
            llm_messages.append({"role": "system", "content": agent_memory_prompt})

    # ========== 添加上下文 ==========
    if data.context:
        context_prompt = build_context_prompt(
            user_context=data.context,
            student_info={"id": data.student_id} if data.student_id else None
        )
        if context_prompt:
            llm_messages.append({"role": "system", "content": context_prompt})

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
    # 顺序：用户问题(文本) -> 图片 -> 文档内容
    if file_messages or file_text_contents:
        user_content = [{"type": "text", "text": data.message}]
        for block in file_messages:
            user_content.append(block)
        if file_text_contents:
            user_content.append({"type": "text", "text": "【上传文档内容】\n" + "\n---\n".join(file_text_contents)})
        llm_messages.append({"role": "user", "content": user_content})
    else:
        llm_messages.append({"role": "user", "content": data.message})

    tool_calls_log = []  # 定义在前面，供下载检测逻辑使用

    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"[Agent Chat] agent_type={agent_type}, has_tools={has_tools}, tool_names={tool_names_list}")

    requested_model = data.model or agent.get("model") or "kimi-k2.5"
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
                    response_text = _extract_content(choices[0].get("message") or {}) or "（无回复）"
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

    # ========== 保存记忆（钩子后置处理） ==========
    if memory_enabled and data.use_memory:
        # 保存会话记忆
        add_session_memory(
            session_id=session_id,
            content=f"用户: {data.message}\n助手: {response_text}",
            importance=0.8,
            tags=["conversation"]
        )

        # 保存 Agent 持久记忆（重要信息）
        if tool_calls_log:
            tool_names = [tc["tool"] for tc in tool_calls_log]
            add_session_memory(
                session_id=f"agent_{agent['id']}",
                content=f"本会话使用了工具: {', '.join(tool_names)}",
                importance=0.5,
                tags=["tool_usage"]
            )

    # 钩子后置处理
    if data.enable_hooks:
        await process_response(response_text, {
            "agent_id": agent["id"],
            "agent_type": agent_type,
            "session_id": session_id,
            "student_id": data.student_id,
            "tool_calls_count": len(tool_calls_log) if tool_calls_log else 0
        })

    return ResponseModel(
        code=200,
        message="success",
        data={
            "response": response_text,
            "session_id": session_id,
            "agent_name": agent["name"],
            "agent_id": agent["id"],
            "agent_type": agent_type,
            "history": history,
            "tool_calls_log": tool_calls_log if tool_calls_log else None,
        },
    )


# ========== 流式对话接口 ==========

@router.post("/chat/stream")
async def agent_chat_stream(data: ChatRequest):
    """Agent 流式对话接口 - 实时输出工具执行状态和AI回复"""
    from fastapi.responses import StreamingResponse

    agents = _load_agents()

    # 按 updated_at 排序，获取最新的 Agent
    if not agents:
        return ResponseModel(code=404, message="请先创建智能体")

    agents.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    current_agent = agents[0]

    session_id = data.session_id or str(uuid4())
    history = _load_session(session_id)

    # 优先使用前端传入的配置，否则回退到 Agent 配置
    agent_type = data.agent_type or current_agent.get("agent_type", "tutor")
    memory_enabled = data.use_memory if data.use_memory is not None else current_agent.get("memory_enabled", True)
    custom_prompt = data.custom_prompt or current_agent.get("prompt", "")
    personality = data.personality or current_agent.get("personality", "balanced")

    async def generate_stream():
        """生成流式响应"""
        import logging
        from common.integration.kimi import kimi_client
        logger = logging.getLogger(__name__)

        try:
            # 发送开始信号
            yield f"data: {json.dumps({'type': 'start', 'session_id': session_id}, ensure_ascii=False)}\n\n"

            # 处理上传的文件
            file_messages = []
            file_text_contents = []
            if data.files:
                for i, f in enumerate(data.files):
                    file_type = f.get("type", "application/octet-stream")
                    file_data = f.get("data", "")
                    data_len = len(file_data) if file_data else 0
                    if not file_data:
                        logger.warning(f"[AgentChat] 文件 {i} 数据为空，跳过")
                        continue
                    if file_type.startswith("image/"):
                        data_url = f"data:{file_type};base64,{file_data}"
                        # 验证 base64 完整性（长度 % 4 应该等于 0，或带 = padding）
                        import base64 as _b64_mod
                        try:
                            _b64_mod.b64decode(file_data[: min(len(file_data), 64)] + "==")
                            logger.info(
                                f"[AgentChat] 图片 {i} base64 验证通过: "
                                f"mime={file_type}, total_len={data_len}, "
                                f"preview={file_data[:20]}..."
                            )
                        except Exception as e:
                            logger.error(
                                f"[AgentChat] 图片 {i} base64 验证失败: {e}, "
                                f"mime={file_type}, total_len={data_len}, preview={file_data[:20]}..."
                            )
                        file_messages.append({
                            "type": "image_url",
                            "image_url": {"url": data_url, "detail": "high"},
                        })
                        logger.info(f"[AgentChat] 图片 {i} 已转换为 image_url: type={file_type}, url_len={len(data_url)}")
                    else:
                        # 文档使用 file-extract 获取文本
                        logger.info(f"[AgentChat] 文档 {i} 开始上传: type={file_type}")
                        file_id = await kimi_client.upload_file(file_data, file_type, "file-extract")
                        if file_id:
                            content = await kimi_client.get_file_content(file_id)
                            if content:
                                file_text_contents.append(content[:20000])
                                logger.info(f"[AgentChat] 文档 {i} 内容获取成功: content_len={len(content)}")
                            else:
                                logger.warning(f"[AgentChat] 文档 {i} 内容获取失败: file_id={file_id}")
                        else:
                            logger.warning(f"[AgentChat] 文档 {i} 上传失败: type={file_type}")

            # 构建用户消息（支持多模态）
            # 顺序：用户问题(文本) -> 图片 -> 文档内容
            if file_messages or file_text_contents:
                user_content = [{"type": "text", "text": data.message}]
                for b in file_messages:
                    user_content.append({"type": "image_url", "image_url": b["image_url"]})
                if file_text_contents:
                    user_content.append({"type": "text", "text": "【上传文档内容】\n" + "\n---\n".join(file_text_contents)})
            else:
                user_content = data.message

            # 保存用户消息（存储文本形式用于历史）
            history.append({
                "role": "user",
                "content": data.message,
                "time": datetime.utcnow().isoformat(),
            })
            _save_session(session_id, history)

            # 构建消息
            enabled_tools = current_agent.get("enabled_tools", [])
            effective_custom_prompt = data.custom_prompt or current_agent.get("prompt", "")
            from services.agent.prompts import build_personality_prompt
            system_prompt = build_agent_system_prompt(
                agent_type,
                effective_custom_prompt,
                enabled_tools,
                personality
            )

            if len(file_messages) > 1:
                image_hints = (
                    "\n\n【重要：用户上传了多张图片】请在本条回复中**依次**阅读每张 image_url 并分析；"
                    "**不要**使用 delegate_task 处理图片（子代理看不到图片）。"
                )
                system_prompt += image_hints

            tools = get_tools_for_agent(enabled_tools, agent_type)
            has_tools = len(tools) > 0

            # 构建 LLM 消息
            llm_messages = [{"role": "system", "content": system_prompt}]

            # 添加记忆
            if memory_enabled:
                session_memory = get_session_memory(session_id, limit=5)
                if session_memory:
                    memory_prompt = build_memory_prompt(session_memory, scope="session")
                    llm_messages.append({"role": "system", "content": memory_prompt})

            # 添加历史消息（仅文本形式）
            for msg in history[:-1]:
                llm_messages.append({"role": msg["role"], "content": msg["content"]})

            # 添加用户消息（多模态格式）
            llm_messages.append({"role": "user", "content": user_content})

            # 打印发送给 Kimi 的消息结构（调试用）
            for i, m in enumerate(llm_messages):
                role = m.get("role", "?")
                c = m.get("content", "")
                if isinstance(c, str):
                    logger.info(f"[AgentChat] → Kimi msg[{i}] role={role} type=str len={len(c)}")
                    if i == 0:  # system prompt 打印前 500 字
                        logger.info(f"[AgentChat] → Kimi system_prompt(前500字): {c[:500]}")
                elif isinstance(c, list):
                    types = [b.get("type") if isinstance(b, dict) else type(b).__name__ for b in c]
                    logger.info(f"[AgentChat] → Kimi msg[{i}] role={role} type=list blocks={types}")
                    for j, block in enumerate(c):
                        if isinstance(block, dict) and block.get("type") == "image_url":
                            url = block.get("image_url", {}).get("url", "")
                            logger.info(f"[AgentChat] → Kimi msg[{i}] block[{j}] image_url url_len={len(url)}")
                else:
                    logger.info(f"[AgentChat] → Kimi msg[{i}] role={role} type={type(c).__name__}")

            # 获取模型（图片模式下强制使用视觉模型）
            requested_model = data.model or current_agent.get("model") or "kimi-k2.5"
            llm_model = requested_model
            if file_messages and llm_model not in KIMI_VISION_MODELS:
                llm_model = "kimi-k2.5"
                logger.info(f"[AgentChat] 模型已切换: {requested_model} -> {llm_model} (因为包含 {len(file_messages)} 张图片)")
            else:
                logger.info(f"[AgentChat] 使用模型: {llm_model}, KIMI_VISION_MODELS={KIMI_VISION_MODELS}")

            logger.info(f"[AgentChat] 最终使用模型: {llm_model}, file_messages数量: {len(file_messages)}, file_text_contents数量: {len(file_text_contents)}")

            response_text = ""
            tool_calls_log = []
            messages_history = []

            # 定义输出函数
            def stream_output(chunk):
                yield f"data: {json.dumps({'type': 'content', 'content': chunk}, ensure_ascii=False)}\n\n"

            if has_tools:
                # 带工具调用的流式处理
                logger.info(f"[AgentChat] tools enabled: {[t.get('function', {}).get('name') for t in tools]}")
                for call_count in range(MAX_TOOL_CALLS):
                    # 调用 LLM（每次都重新调用）
                    result = await kimi_client.chat(
                        messages=llm_messages,
                        tools=tools,
                        model=llm_model,
                        temperature=1.0,
                        max_tokens=data.max_tokens or 4096,
                        top_p=1.0,
                        frequency_penalty=data.frequency_penalty or 0.0,
                        presence_penalty=data.presence_penalty or 0.0
                    )

                    if "error" in result:
                        detail = result.get("detail") or ""
                        err_text = f"抱歉，调用 AI 服务时出错：{result['error']}"
                        if detail:
                            err_text = err_text + " " + detail[:800]
                        yield f"data: {json.dumps({'type': 'content', 'content': err_text}, ensure_ascii=False)}\n\n"
                        response_text = err_text
                        break

                    choices = result.get("choices", [])
                    if not choices:
                        err_text = "抱歉，没有收到 AI 的回复。"
                        yield f"data: {json.dumps({'type': 'content', 'content': err_text}, ensure_ascii=False)}\n\n"
                        response_text = err_text
                        break

                    message = choices[0].get("message", {})

                    # 检查是否有 tool_calls
                    if "tool_calls" in message and message["tool_calls"]:
                        for tc in message["tool_calls"]:
                            tool_name = tc["function"]["name"]
                            tool_args = tc["function"].get("arguments", {})

                            try:
                                if isinstance(tool_args, str):
                                    tool_args = json.loads(tool_args)
                            except json.JSONDecodeError:
                                tool_args = {}

                            # 发送工具开始
                            is_subagent = (tool_name == "delegate_task")
                            if is_subagent:
                                logger.info(f"[AgentChat] delegate_task called with args: {tool_args}")
                            yield f"data: {json.dumps({
                                'type': 'tool_start',
                                'tool': tool_name,
                                'args': tool_args,
                                'is_subagent': is_subagent
                            }, ensure_ascii=False)}\n\n"

                            # 添加 assistant 的 tool_call 消息
                            tool_call_msg = {
                                "role": "assistant",
                                "content": None,
                                "tool_calls": [tc]
                            }
                            if message.get("reasoning_content"):
                                tool_call_msg["reasoning_content"] = message.get("reasoning_content")
                            llm_messages.append(tool_call_msg)

                            # 执行工具
                            backend_url = f"http://{settings.HOST or '127.0.0.1'}:{settings.PORT or 8000}"
                            tool_result = await execute_tool(tool_name, tool_args, base_url=backend_url)

                            tool_calls_log.append({
                                "tool": tool_name,
                                "arguments": tool_args,
                                "result": tool_result
                            })

                            # 发送工具结束
                            yield f"data: {json.dumps({
                                'type': 'tool_end',
                                'tool': tool_name,
                                'result': tool_result
                            }, ensure_ascii=False)}\n\n"
                            
                            if is_subagent:
                                logger.info(f"[AgentChat] delegate_task returned, summary: {tool_result.get('summary', 'N/A')[:200] if isinstance(tool_result, dict) else 'N/A'}")

                            # 添加 tool 角色消息
                            llm_messages.append({
                                "role": "tool",
                                "tool_call_id": tc["id"],
                                "content": json.dumps(tool_result, ensure_ascii=False)
                            })

                        # 继续循环
                        continue

                    # 普通文本回复 - 流式输出
                    content = _extract_content(message)
                    if content:
                        # 逐段输出，模拟打字效果
                        for i in range(0, len(content), 5):
                            chunk = content[i:i+5]
                            response_text += chunk
                            yield f"data: {json.dumps({'type': 'content', 'content': chunk}, ensure_ascii=False)}\n\n"
                            await asyncio.sleep(0.01)

                    break  # 完成，退出循环

                else:
                    # 达到最大调用次数
                    err_text = "抱歉，执行了太多工具调用，请简化你的问题。"
                    yield f"data: {json.dumps({'type': 'content', 'content': err_text}, ensure_ascii=False)}\n\n"
                    response_text = err_text
            else:
                # 无工具：直接流式调用
                full_response = ""

                async for chunk in kimi_client.chat_stream(
                    messages=llm_messages,
                    temperature=1.0,
                    max_tokens=data.max_tokens or 4096,
                    top_p=1.0,
                    model=llm_model,
                    tools=None
                ):
                    if chunk.startswith("data: "):
                        data_str = chunk[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            parsed = json.loads(data_str)
                            if "choices" in parsed:
                                delta = parsed["choices"][0].get("delta", {})
                                # 同时检查 content 和 reasoning_content（kimi-k2.5 主要在 reasoning_content 返回）
                                delta_content = delta.get("content", "")
                                if not delta_content:
                                    delta_content = delta.get("reasoning_content", "")
                                if delta_content:
                                    full_response += delta_content
                                    yield f"data: {json.dumps({'type': 'content', 'content': delta_content}, ensure_ascii=False)}\n\n"
                        except json.JSONDecodeError:
                            continue

                response_text = full_response

            # 发送最终回复
            if response_text:
                yield f"data: {json.dumps({'type': 'content', 'content': response_text}, ensure_ascii=False)}\n\n"

            # 保存历史
            history.append({
                "role": "assistant",
                "content": response_text,
                "time": datetime.utcnow().isoformat(),
            })
            _save_session(session_id, history)

            # 保存记忆
            if memory_enabled and data.use_memory:
                add_session_memory(
                    session_id=session_id,
                    content=f"用户: {data.message}\n助手: {response_text}",
                    importance=0.8,
                    tags=["conversation"]
                )

            # 发送完成信号
            yield f"data: {json.dumps({
                'type': 'done',
                'session_id': session_id,
                'agent_name': current_agent["name"],
                'agent_id': current_agent["id"],
                'tool_calls_log': tool_calls_log if tool_calls_log else None
            }, ensure_ascii=False)}\n\n"

        except Exception as e:
            import traceback
            logger.error(f"流式响应异常: {str(e)}\n{traceback.format_exc()}")
            yield f"data: {json.dumps({'type': 'error', 'error': f'服务器错误: {str(e)}'}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
