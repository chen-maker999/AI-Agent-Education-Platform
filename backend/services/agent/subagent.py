"""Agent 子代理和任务系统 - 支持 Fork 子代理和异步执行"""

import asyncio
import json
from typing import Dict, List, Optional, Any, AsyncGenerator
from enum import Enum
from uuid import uuid4
from datetime import datetime


class TaskType(str, Enum):
    """任务类型"""
    LOCAL_BASH = "local_bash"      # 本地 Bash 任务
    LOCAL_AGENT = "local_agent"    # 本地代理
    ASYNC_AGENT = "async_agent"   # 异步代理
    SUBAGENT = "subagent"          # 子代理


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    KILLED = "killed"


class Task:
    """任务对象"""
    def __init__(
        self,
        task_id: str,
        task_type: TaskType,
        agent_id: str = None,
        agent_type: str = "general",
        prompt: str = "",
        enabled_tools: List[str] = None,
        session_id: str = None,
        parent_task_id: str = None,
        status: TaskStatus = TaskStatus.PENDING,
        result: Any = None,
        error: str = None,
        created_at: str = None,
        started_at: str = None,
        completed_at: str = None,
        metadata: Dict[str, Any] = None
    ):
        self.task_id = task_id
        self.task_type = task_type
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.prompt = prompt
        self.enabled_tools = enabled_tools or []
        self.session_id = session_id or str(uuid4())
        self.parent_task_id = parent_task_id
        self.status = status
        self.result = result
        self.error = error
        self.created_at = created_at or datetime.utcnow().isoformat()
        self.started_at = started_at
        self.completed_at = completed_at
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type.value if isinstance(self.task_type, TaskType) else self.task_type,
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "prompt": self.prompt,
            "enabled_tools": self.enabled_tools,
            "session_id": self.session_id,
            "parent_task_id": self.parent_task_id,
            "status": self.status.value if isinstance(self.status, TaskStatus) else self.status,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        return cls(
            task_id=data.get("task_id"),
            task_type=TaskType(data.get("task_type", "local_agent")),
            agent_id=data.get("agent_id"),
            agent_type=data.get("agent_type", "general"),
            prompt=data.get("prompt", ""),
            enabled_tools=data.get("enabled_tools", []),
            session_id=data.get("session_id"),
            parent_task_id=data.get("parent_task_id"),
            status=TaskStatus(data.get("status", "pending")),
            result=data.get("result"),
            error=data.get("error"),
            created_at=data.get("created_at"),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            metadata=data.get("metadata", {})
        )


class TaskManager:
    """任务管理器"""
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self._running_tasks: Dict[str, asyncio.Task] = {}
    
    def create_task(
        self,
        task_type: TaskType,
        agent_id: str = None,
        agent_type: str = "general",
        prompt: str = "",
        enabled_tools: List[str] = None,
        session_id: str = None,
        parent_task_id: str = None,
        metadata: Dict[str, Any] = None
    ) -> Task:
        """创建任务"""
        task = Task(
            task_id=str(uuid4()),
            task_type=task_type,
            agent_id=agent_id,
            agent_type=agent_type,
            prompt=prompt,
            enabled_tools=enabled_tools,
            session_id=session_id,
            parent_task_id=parent_task_id,
            metadata=metadata
        )
        
        self.tasks[task.task_id] = task
        return task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        return self.tasks.get(task_id)
    
    def update_task_status(self, task_id: str, status: TaskStatus):
        """更新任务状态"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = status
            
            if status == TaskStatus.RUNNING and not task.started_at:
                task.started_at = datetime.utcnow().isoformat()
            elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.KILLED]:
                task.completed_at = datetime.utcnow().isoformat()
    
    def set_task_result(self, task_id: str, result: Any = None, error: str = None):
        """设置任务结果"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.result = result
            task.error = error
            task.status = TaskStatus.FAILED if error else TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow().isoformat()
    
    def list_tasks(
        self,
        status: TaskStatus = None,
        agent_id: str = None,
        parent_task_id: str = None
    ) -> List[Task]:
        """列出任务"""
        result = list(self.tasks.values())
        
        if status:
            result = [t for t in result if t.status == status]
        if agent_id:
            result = [t for t in result if t.agent_id == agent_id]
        if parent_task_id:
            result = [t for t in result if t.parent_task_id == parent_task_id]
        
        # 按创建时间降序
        result.sort(key=lambda x: x.created_at, reverse=True)
        
        return result
    
    async def run_subagent(
        self,
        prompt: str,
        agent_type: str = "general",
        enabled_tools: List[str] = None,
        parent_task_id: str = None,
        is_async: bool = False,
        metadata: Dict[str, Any] = None
    ) -> Task:
        """
        运行子代理
        
        Args:
            prompt: 子代理指令
            agent_type: 子代理类型
            enabled_tools: 启用的工具
            parent_task_id: 父任务 ID
            is_async: 是否异步执行
            metadata: 额外元数据
        
        Returns:
            任务对象
        """
        task_type = TaskType.ASYNC_AGENT if is_async else TaskType.SUBAGENT
        
        task = self.create_task(
            task_type=task_type,
            agent_type=agent_type,
            prompt=prompt,
            enabled_tools=enabled_tools,
            parent_task_id=parent_task_id,
            metadata=metadata
        )
        
        if is_async:
            # 异步执行
            asyncio_task = asyncio.create_task(self._execute_subagent(task))
            self._running_tasks[task.task_id] = asyncio_task
        else:
            # 同步执行
            await self._execute_subagent(task)
        
        return task
    
    async def _execute_subagent(self, task: Task) -> Dict[str, Any]:
        """执行子代理（直接调用 Kimi API，不走 agent_chat 避免循环导入）"""
        from common.integration.kimi import kimi_client
        from services.agent.prompts import build_agent_system_prompt
        from services.agent.tools.registry import get_tools_for_agent
        import logging
        logger = logging.getLogger(__name__)

        try:
            self.update_task_status(task.task_id, TaskStatus.RUNNING)

            # 构建子代理的 system prompt 和工具
            system_prompt = build_agent_system_prompt(
                task.agent_type or "general",
                custom_prompt="",
                enabled_tools=task.enabled_tools or []
            )
            tools = get_tools_for_agent(task.enabled_tools or [], task.agent_type or "general")

            # 构造消息
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": task.prompt}
            ]

            result = await kimi_client.chat(
                messages=messages,
                tools=tools,
                model="kimi-k2.5",
                temperature=1.0,
                max_tokens=4096,
                top_p=1.0
            )

            if "error" in result:
                self.set_task_result(task.task_id, error=result.get("detail") or result["error"])
                return {"error": result.get("detail") or result["error"]}

            choices = result.get("choices", [])
            if choices:
                message = choices[0].get("message", {})
                content = message.get("content", "")
                self.set_task_result(task.task_id, result={"response": content, "raw": message})
                return {"response": content, "raw": message}

            self.set_task_result(task.task_id, error="子代理未返回内容")
            return {"error": "子代理未返回内容"}

        except Exception as e:
            logger.error(f"[SubAgent] 执行失败: {e}")
            self.set_task_result(task.task_id, error=str(e))
            return {"error": str(e)}
        finally:
            # 清理运行中的任务
            if task.task_id in self._running_tasks:
                del self._running_tasks[task.task_id]
    
    async def kill_task(self, task_id: str) -> bool:
        """终止任务"""
        if task_id in self._running_tasks:
            self._running_tasks[task_id].cancel()
            self.update_task_status(task_id, TaskStatus.KILLED)
            return True
        return False
    
    def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务结果"""
        task = self.get_task(task_id)
        if not task:
            return None
        
        return {
            "task_id": task.task_id,
            "status": task.status.value if isinstance(task.status, TaskStatus) else task.status,
            "result": task.result,
            "error": task.error,
            "started_at": task.started_at,
            "completed_at": task.completed_at
        }


# Fork 子代理模板
FORK_SUBAGENT_TEMPLATE = """
STOP. READ THIS FIRST.

You are a forked worker process. You are NOT the main agent.

RULES (non-negotiable):
1. Do NOT spawn sub-agents; execute directly.
2. Do NOT converse, ask questions, or suggest next steps
3. Do NOT editorialize or add meta-commentary
4. USE your tools directly: Bash, Read, Write, etc.
5. Keep your report under 500 words

Output format:
Scope: <echo back your assigned scope>
Result: <the answer or key findings>
Key files: <relevant file paths>
"""


def build_fork_directive(directive: str, scope: str = None) -> str:
    """
    构建 Fork 子代理指令
    
    Args:
        directive: 具体指令
        scope: 工作范围描述
    
    Returns:
        完整的 Fork 子代理提示
    """
    template = FORK_SUBAGENT_TEMPLATE
    
    if scope:
        template = template.replace(
            "<echo back your assigned scope>",
            scope
        )
    
    return template + f"\n\n<FORK_DIRECTIVE>{directive}</FORK_DIRECTIVE>"


# 全局任务管理器
task_manager = TaskManager()


# ===== 便捷函数 =====

def create_subagent_task(
    prompt: str,
    agent_type: str = "general",
    enabled_tools: List[str] = None,
    parent_task_id: str = None
) -> Task:
    """创建子代理任务"""
    return task_manager.create_task(
        task_type=TaskType.SUBAGENT,
        agent_type=agent_type,
        prompt=prompt,
        enabled_tools=enabled_tools,
        parent_task_id=parent_task_id
    )


async def run_async_subagent(
    prompt: str,
    agent_type: str = "general",
    enabled_tools: List[str] = None,
    parent_task_id: str = None
) -> Task:
    """异步运行子代理"""
    return await task_manager.run_subagent(
        prompt=prompt,
        agent_type=agent_type,
        enabled_tools=enabled_tools,
        parent_task_id=parent_task_id,
        is_async=True
    )


def get_task(task_id: str) -> Optional[Task]:
    """获取任务"""
    return task_manager.get_task(task_id)


def get_task_status(task_id: str) -> Optional[str]:
    """获取任务状态"""
    task = task_manager.get_task(task_id)
    return task.status.value if task else None


def list_running_tasks() -> List[Task]:
    """列出运行中的任务"""
    return task_manager.list_tasks(status=TaskStatus.RUNNING)


def list_pending_tasks() -> List[Task]:
    """列出待处理的任务"""
    return task_manager.list_tasks(status=TaskStatus.PENDING)
