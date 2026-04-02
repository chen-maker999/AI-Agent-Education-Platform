"""Agent 工具注册表 - 统一管理所有工具定义和执行（增强版）"""

import json
import asyncio
import httpx
from typing import Dict, Any, Optional, Callable, List, Set
from pathlib import Path
from enum import Enum


class ToolCategory(str, Enum):
    """工具分类"""
    FILE = "file"           # 文件操作
    SEARCH = "search"       # 搜索相关
    KNOWLEDGE = "knowledge" # 知识库
    SYSTEM = "system"       # 系统操作
    WEB = "web"            # 联网功能


class ToolPermission(str, Enum):
    """工具权限级别"""
    SAFE = "safe"           # 安全操作
    CAUTION = "caution"     # 需要谨慎
    RESTRICTED = "restricted"  # 受限操作


class ToolDefinition:
    """工具定义类"""
    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        category: ToolCategory,
        permission: ToolPermission,
        parameters: Dict[str, Any],
        required: List[str],
        optional: List[str] = None,
        examples: List[Dict[str, str]] = None,
        danger_level: str = "safe"  # safe, warning, danger
    ):
        self.id = id
        self.name = name
        self.description = description
        self.category = category
        self.permission = permission
        self.parameters = parameters
        self.required = required
        self.optional = optional or []
        self.examples = examples or []
        self.danger_level = danger_level

    def to_openai_format(self) -> Dict[str, Any]:
        """转换为 OpenAI function calling 格式"""
        props = {}
        for param_name, param_info in self.parameters.items():
            props[param_name] = {
                "type": param_info.get("type", "string"),
                "description": param_info.get("description", "")
            }
            if "enum" in param_info:
                props[param_name]["enum"] = param_info["enum"]
            if "default" in param_info:
                props[param_name]["default"] = param_info["default"]
        
        return {
            "type": "function",
            "function": {
                "name": self.id,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": props,
                    "required": self.required
                }
            }
        }


# 增强的工具定义
TOOL_DEFINITIONS_LIST: List[ToolDefinition] = [
    # ===== 文件操作工具 =====
    ToolDefinition(
        id="reading",
        name="阅读",
        description="读取用户在对话中上传的文件内容。当用户上传了文件并询问相关问题时使用此工具。",
        category=ToolCategory.FILE,
        permission=ToolPermission.SAFE,
        danger_level="safe",
        parameters={
            "path": {"type": "string", "description": "要读取的文件路径或文件名"},
            "keyword": {"type": "string", "description": "搜索文件内容的关键词（可选）"}
        },
        required=["path"],
        examples=[
            {"scenario": "读取上传的PDF文件", "arguments": '{"path": "document.pdf"}'},
            {"scenario": "搜索文件中的关键词", "arguments": '{"path": "notes.txt", "keyword": "重点"}'}
        ]
    ),
    ToolDefinition(
        id="editing",
        name="编辑",
        description="修改用户在对话中上传的文件内容。当用户要求修改、补充或更正上传的文件时使用此工具。",
        category=ToolCategory.FILE,
        permission=ToolPermission.CAUTION,
        danger_level="warning",
        parameters={
            "path": {"type": "string", "description": "要编辑的文件路径或文件名"},
            "action": {
                "type": "string",
                "enum": ["create", "edit", "delete"],
                "description": "操作类型：create创建新文件，edit编辑现有文件，delete删除文件"
            },
            "content": {"type": "string", "description": "文件完整内容（用于创建新文件）"},
            "old_string": {"type": "string", "description": "要替换的旧内容片段（用于编辑）"},
            "new_string": {"type": "string", "description": "替换后的新内容（用于编辑）"}
        },
        required=["path", "action"],
        examples=[
            {"scenario": "创建新文件", "arguments": '{"path": "test.py", "action": "create", "content": "# Hello World"}'},
            {"scenario": "编辑现有文件", "arguments": '{"path": "notes.txt", "action": "edit", "old_string": "旧内容", "new_string": "新内容"}'}
        ]
    ),
    
    # ===== 搜索工具 =====
    ToolDefinition(
        id="knowledge_search",
        name="知识库检索",
        description="搜索知识库中的相关资料。当用户询问需要查找资料、解释概念、回答与已上传文档相关的问题时使用。",
        category=ToolCategory.KNOWLEDGE,
        permission=ToolPermission.SAFE,
        danger_level="safe",
        parameters={
            "query": {"type": "string", "description": "搜索查询词，尽量使用与用户问题相关的关键词"},
            "top_k": {"type": "integer", "description": "返回的最相关结果数量", "default": 5}
        },
        required=["query"],
        examples=[
            {"scenario": "查找相关知识", "arguments": '{"query": "机器学习基础", "top_k": 5}'}
        ]
    ),
    
    # ===== 知识库工具 =====
    ToolDefinition(
        id="download_to_knowledge",
        name="下载资料",
        description="从网上下载资料（PDF、网页等）并保存到知识库。使用course_id='default'表示保存到默认知识库。",
        category=ToolCategory.KNOWLEDGE,
        permission=ToolPermission.CAUTION,
        danger_level="warning",
        parameters={
            "url": {"type": "string", "description": "要下载的 URL（支持 PDF、网页、文档链接）"},
            "filename": {"type": "string", "description": "保存到知识库的文件名（不含扩展名）"},
            "course_id": {"type": "string", "description": "知识库课程 ID", "default": "default"}
        },
        required=["url", "filename"],
        examples=[
            {"scenario": "保存PDF到知识库", "arguments": '{"url": "https://example.com/paper.pdf", "filename": "学术论文"}'},
            {"scenario": "保存网页到知识库", "arguments": '{"url": "https://zh.wikipedia.org/wiki/人工智能", "filename": "AI百科"}'}
        ]
    ),
    
    # ===== 系统工具 =====
    ToolDefinition(
        id="terminal",
        name="终端",
        description="在终端运行命令并获取状态和结果。当用户要求运行代码、安装依赖、执行命令时使用。",
        category=ToolCategory.SYSTEM,
        permission=ToolPermission.RESTRICTED,
        danger_level="danger",
        parameters={
            "command": {"type": "string", "description": "要执行的终端命令"},
            "cwd": {"type": "string", "description": "命令执行的工作目录（可选）"},
            "timeout": {"type": "integer", "description": "超时秒数", "default": 30}
        },
        required=["command"],
        examples=[
            {"scenario": "运行Python脚本", "arguments": '{"command": "python test.py", "timeout": 60}'},
            {"scenario": "安装依赖", "arguments": '{"command": "pip install requests"}'}
        ]
    ),
    ToolDefinition(
        id="preview",
        name="预览",
        description="在生成前端结果后提供预览入口。用于展示生成的HTML或URL预览。",
        category=ToolCategory.SYSTEM,
        permission=ToolPermission.SAFE,
        danger_level="safe",
        parameters={
            "title": {"type": "string", "description": "预览标题"},
            "url": {"type": "string", "description": "预览链接"},
            "description": {"type": "string", "description": "预览描述"}
        },
        required=["title"],
        examples=[
            {"scenario": "预览生成的页面", "arguments": '{"title": "生成的页面", "url": "https://example.com/page.html"}'}
        ]
    ),

    # ===== Tavily 搜索工具 =====
    ToolDefinition(
        id="tavily_search",
        name="Tavily搜索",
        description="使用 Tavily API 进行深度网络搜索。当用户询问最新信息、新闻、实时数据、技术文档等时使用。比普通搜索更全面、更准确。",
        category=ToolCategory.SEARCH,
        permission=ToolPermission.SAFE,
        danger_level="safe",
        parameters={
            "query": {"type": "string", "description": "搜索关键词，尽量使用完整的问句"},
            "max_results": {"type": "integer", "description": "最大返回结果数 (1-10)", "default": 5}
        },
        required=["query"],
        examples=[
            {"scenario": "搜索最新技术文档", "arguments": '{"query": "Python 3.12 new features", "max_results": 5}'},
            {"scenario": "搜索新闻", "arguments": '{"query": "2024 AI developments", "max_results": 10}'}
        ]
    ),
    # ===== 子代理委托工具 =====
    ToolDefinition(
        id="delegate_task",
        name="委托任务",
        description="当你需要同时处理多个独立子任务时，使用此工具将复杂问题分解给子代理并行处理。例如：用户要求同时回答多个问题、进行多步分析、搜索多个主题。每个子任务独立执行后，结果会汇总返回给你。仅在任务确实可以分解时使用，不要过度使用。",
        category=ToolCategory.SYSTEM,
        permission=ToolPermission.SAFE,
        danger_level="safe",
        parameters={
            "subtasks": {
                "type": "array",
                "description": "子任务列表，每个任务包含 task_id（唯一标识）和 prompt（具体指令）",
                "items": {
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string", "description": "子任务唯一标识符（如 'search_1', 'analysis_2'）"},
                        "prompt": {"type": "string", "description": "子任务的详细指令，尽量具体明确"}
                    },
                    "required": ["task_id", "prompt"]
                }
            }
        },
        required=["subtasks"],
        examples=[
            {"scenario": "并行搜索多个主题", "arguments": '{"subtasks": [{"task_id": "search_1", "prompt": "搜索 Python 异步编程的最新特性"}, {"task_id": "search_2", "prompt": "搜索 FastAPI 性能优化技巧"}]}'},
            {"scenario": "多角度分析", "arguments": '{"subtasks": [{"task_id": "pro", "prompt": "分析使用 React 的优势"}, {"task_id": "con", "prompt": "分析使用 React 的潜在问题"}]}'}
        ]
    ),
]


# 工具 ID 到函数名的映射
TOOL_ID_TO_NAME = {
    "reading": "reading",
    "editing": "editing",
    "terminal": "terminal",
    "preview": "preview",
    "tavily_search": "tavily_search",
    "download_to_knowledge": "download_to_knowledge",
    "knowledge_search": "knowledge_search",
    "delegate_task": "delegate_task"
}


# ===== 工具权限控制 =====

# 所有 Agent 默认禁用的工具（高危工具）
ALL_AGENT_DISALLOWED_TOOLS: Set[str] = {
    "terminal"  # 终端默认禁用，需明确启用
}

# 自定义 Agent 禁用工具
CUSTOM_AGENT_DISALLOWED_TOOLS: Set[str] = {
    "terminal"
}

# 各类型 Agent 禁用工具映射
AGENT_TYPE_DISALLOWED_TOOLS: Dict[str, Set[str]] = {
    "explorer": {"editing", "terminal"},  # 探索代理禁用编辑和终端
    "planner": {"editing", "terminal"},   # 计划代理禁用编辑和终端
    "verifier": set(),                     # 验证代理不禁用（必须用 set()）
    "tutor": {"editing", "terminal"},     # 辅导代理禁用编辑和终端
    "grader": {"terminal"},               # 批改代理禁用终端
    "general": set(),                      # 通用代理不禁用（必须用 set()）
    "custom": {"terminal"}                 # 自定义代理禁用终端
}

# 各类型 Agent 推荐工具
AGENT_TYPE_RECOMMENDED_TOOLS: Dict[str, List[str]] = {
    "explorer": ["reading", "tavily_search", "knowledge_search", "delegate_task"],
    "planner": ["reading", "tavily_search", "knowledge_search", "delegate_task"],
    "verifier": ["reading", "tavily_search", "knowledge_search"],
    "tutor": ["tavily_search", "knowledge_search", "preview", "delegate_task"],
    "grader": ["reading", "editing", "knowledge_search", "delegate_task"],
    "general": ["reading", "editing", "terminal", "tavily_search", "knowledge_search", "delegate_task"],
    "custom": ["reading", "tavily_search", "knowledge_search", "delegate_task"]
}


def get_tools_for_agent(
    enabled_tool_ids: List[str],
    agent_type: str = "general",
    exclude_disallowed: bool = True
) -> List[Dict[str, Any]]:
    """
    获取 Agent 启用的工具定义列表

    Args:
        enabled_tool_ids: Agent 启用的工具 ID 列表
        agent_type: Agent 类型
        exclude_disallowed: 是否排除禁用工具

    Returns:
        工具定义列表（OpenAI 格式）
    """
    # 获取基础启用的工具
    enabled_names = set(TOOL_ID_TO_NAME.get(tid, tid) for tid in enabled_tool_ids)

    # 如果需要，排除禁用工具
    if exclude_disallowed:
        # 合并类型禁用工具和全局禁用工具
        type_disallowed = AGENT_TYPE_DISALLOWED_TOOLS.get(agent_type, set()) or set()
        all_disallowed = set(ALL_AGENT_DISALLOWED_TOOLS) | type_disallowed
        enabled_names = enabled_names - all_disallowed

    # 转换为核心工具定义
    core_tools = [t for t in TOOL_DEFINITIONS_LIST if t.id in enabled_names]

    # 转换为 OpenAI 格式
    return [t.to_openai_format() for t in core_tools]


def get_tool_definition(tool_id: str) -> Optional[ToolDefinition]:
    """获取工具定义"""
    for tool in TOOL_DEFINITIONS_LIST:
        if tool.id == tool_id:
            return tool
    return None


def get_tools_by_category(category: ToolCategory) -> List[ToolDefinition]:
    """获取指定分类的所有工具"""
    return [t for t in TOOL_DEFINITIONS_LIST if t.category == category]


def get_tools_by_permission(permission: ToolPermission) -> List[ToolDefinition]:
    """获取指定权限级别的所有工具"""
    return [t for t in TOOL_DEFINITIONS_LIST if t.permission == permission]


def is_tool_allowed(tool_id: str, agent_type: str = "general") -> bool:
    """检查工具是否允许使用"""
    disallowed = AGENT_TYPE_DISALLOWED_TOOLS.get(agent_type, set())
    disallowed.update(ALL_AGENT_DISALLOWED_TOOLS)
    return tool_id not in disallowed


def get_all_tools() -> List[Dict[str, Any]]:
    """获取所有工具定义"""
    return [t.to_openai_format() for t in TOOL_DEFINITIONS_LIST]


def get_tools_metadata() -> List[Dict[str, Any]]:
    """获取所有工具的元数据（包含更多信息）"""
    return [
        {
            "id": t.id,
            "name": t.name,
            "description": t.description,
            "category": t.category.value,
            "permission": t.permission.value,
            "danger_level": t.danger_level,
            "required_params": t.required,
            "optional_params": t.optional,
            "examples": t.examples
        }
        for t in TOOL_DEFINITIONS_LIST
    ]


async def _execute_delegate_task(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    执行委托任务：并行启动多个子代理，最后汇总结果

    Args:
        arguments: {"subtasks": [{"task_id": "...", "prompt": "..."}]}

    Returns:
        {"results": [{"task_id": "...", "status": "success|error", "response": "..."}]}
    """
    from services.agent.subagent import task_manager, TaskType
    import logging
    logger = logging.getLogger(__name__)

    subtasks = arguments.get("subtasks", [])
    if not subtasks:
        return {"error": "subtasks 不能为空"}
    if len(subtasks) > 5:
        return {"error": "subtasks 最多支持 5 个并行子任务"}

    logger.info(f"[delegate_task] 启动 {len(subtasks)} 个并行子任务")
    results = []

    from datetime import datetime
    async def run_one(subtask: Dict[str, Any]) -> Dict[str, Any]:
        task_id = subtask.get("task_id", "unknown")
        prompt = subtask.get("prompt", "unknown")
        launch_time = datetime.utcnow()
        logger.info(f"[delegate_task] [LAUNCH] {task_id} at {launch_time.isoformat()} | prompt preview: {prompt[:50]}...")
        try:
            # 真正的并行：is_async=True，让子代理在后台异步执行
            task = await task_manager.run_subagent(
                prompt=prompt,
                agent_type="general",
                enabled_tools=["reading"],  # 子代理只允许读文件，不允许搜索/改文件
                is_async=True  # 异步执行，不阻塞
            )
            return {
                "task_id": task_id,
                "status": "pending",
                "launch_time": launch_time,
                "task_obj": task  # 暂存 task 对象，后续取结果
            }
        except Exception as e:
            logger.error(f"[delegate_task] subtask {task_id} launch failed: {e}")
            return {
                "task_id": task_id,
                "status": "error",
                "error": str(e)
            }

    # 第一步：并发启动所有子代理（不等结果）
    logger.info(f"[delegate_task] === 开始并发启动 {len(subtasks)} 个子代理 ===")
    launch_all_time = datetime.utcnow()
    launched = await asyncio.gather(*[run_one(s) for s in subtasks])
    launch_done_time = datetime.utcnow()
    elapsed_launch = (launch_done_time - launch_all_time).total_seconds()
    logger.info(f"[delegate_task] === 全部 {len(subtasks)} 个子代理已启动，耗时 {elapsed_launch:.3f}s ===")

    # 第二步：轮询等待所有子代理完成
    pending_tasks = [r for r in launched if r.get("status") == "pending"]
    if pending_tasks:
        logger.info(f"[delegate_task] 开始轮询等待 {len(pending_tasks)} 个子代理完成...")
        poll_start = datetime.utcnow()
        for poll_round in range(60):
            await asyncio.sleep(2)
            running = [t for t in pending_tasks if t["task_obj"].status.value == "running"]
            done_count = len(pending_tasks) - len(running)
            logger.info(f"[delegate_task] [POLL {poll_round+1}] 已完成 {done_count}/{len(pending_tasks)} | running: {len(running)}")
            if not running:
                break
        poll_end = datetime.utcnow()
        logger.info(f"[delegate_task] === 轮询等待完成，耗时 {(poll_end - poll_start).total_seconds():.3f}s ===")

    # 第三步：收集结果
    results = []
    for r in launched:
        if r.get("status") == "pending":
            task = r["task_obj"]
            result_data = task_manager.get_task_result(task.task_id)
            finish_time = datetime.utcnow()
            total_time = (finish_time - r["launch_time"]).total_seconds()
            if result_data.get("error"):
                r["status"] = "error"
                r["error"] = result_data["error"]
                logger.info(f"[delegate_task] [DONE] {r['task_id']} ERROR after {total_time:.3f}s: {result_data['error'][:100]}")
            else:
                r["status"] = "success"
                r["response"] = result_data.get("result", {}).get("response", "")
                resp_len = len(r["response"])
                logger.info(f"[delegate_task] [DONE] {r['task_id']} SUCCESS after {total_time:.3f}s | response length: {resp_len}")
            del r["task_obj"]
            del r["launch_time"]
        results.append(r)

    # 汇总
    summary_lines = [f"### 子任务汇总（共{len(subtasks)}个）"]
    for r in results:
        status_icon = "✓" if r["status"] == "success" else "✗"
        summary_lines.append(f"- [{status_icon}] {r['task_id']}: {r.get('response', r.get('error', ''))[:200]}")

    return {
        "subtasks_count": len(subtasks),
        "results": list(results),
        "summary": "\n".join(summary_lines)
    }


async def execute_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    base_url: str = "http://localhost:8000",
    agent_type: str = "general"
) -> Dict[str, Any]:
    """
    执行工具调用
    
    Args:
        tool_name: 工具名称
        arguments: 工具参数
        base_url: 后端服务地址
        agent_type: Agent 类型（用于权限检查）
    
    Returns:
        工具执行结果
    """
    from common.core.config import settings

    # 权限检查
    if not is_tool_allowed(tool_name, agent_type):
        return {
            "error": f"工具 {tool_name} 在当前 Agent 类型 ({agent_type}) 中被禁用",
            "allowed": False
        }

    # 委托任务由 TaskManager 直接执行，不需要 HTTP 调用
    if tool_name == "delegate_task":
        return await _execute_delegate_task(arguments)

    api_prefix = settings.API_PREFIX

    # 工具名称到 API 端点的映射
    tool_endpoints = {
        "reading": f"{base_url}{api_prefix}/agent/tools/read",
        "editing": f"{base_url}{api_prefix}/agent/tools/edit",
        "terminal": f"{base_url}{api_prefix}/agent/tools/terminal",
        "preview": f"{base_url}{api_prefix}/agent/tools/preview",
        "tavily_search": f"{base_url}{api_prefix}/agent/tools/tavily_search",
        "download_to_knowledge": f"{base_url}{api_prefix}/agent/tools/download_to_knowledge",
        "knowledge_search": f"{base_url}{api_prefix}/agent/tools/knowledge_search",
    }

    if tool_name not in tool_endpoints:
        return {"error": f"未知工具: {tool_name}"}

    try:
        # 设置超时
        timeout = 60.0
        if tool_name == "terminal":
            timeout = arguments.get("timeout", 30)
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                tool_endpoints[tool_name],
                json=arguments,
                headers={"Content-Type": "application/json"}
            )
            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 200:
                    return result.get("data", {})
                else:
                    return {"error": result.get("message", "Unknown error")}
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
    except httpx.RequestError as e:
        return {"error": f"请求失败: {str(e)}"}
    except Exception as e:
        return {"error": f"执行失败: {str(e)}"}


# 保持向后兼容
TOOL_DEFINITIONS = [t.to_openai_format() for t in TOOL_DEFINITIONS_LIST]
