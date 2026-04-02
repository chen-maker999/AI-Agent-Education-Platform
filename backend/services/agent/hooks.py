"""Agent 会话钩子系统 - 支持前置/后置钩子"""

import re
from typing import Dict, List, Optional, Any, Callable, Awaitable
from enum import Enum
from datetime import datetime


class HookType(str, Enum):
    """钩子类型"""
    PRE_MESSAGE = "pre_message"      # 消息前置处理
    POST_MESSAGE = "post_message"   # 消息后置处理
    PRE_TOOL_CALL = "pre_tool_call"  # 工具调用前置
    POST_TOOL_CALL = "post_tool_call"  # 工具调用后置
    PRE_AGENT = "pre_agent"         # Agent 调用前置
    POST_AGENT = "post_agent"       # Agent 调用后置
    ON_ERROR = "on_error"           # 错误处理
    ON_SESSION_END = "on_session_end"  # 会话结束


class HookResult:
    """钩子执行结果"""
    def __init__(
        self,
        success: bool,
        modified: bool = False,
        data: Any = None,
        error: str = None,
        message: str = None
    ):
        self.success = success
        self.modified = modified
        self.data = data
        self.error = error
        self.message = message

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "modified": self.modified,
            "data": self.data,
            "error": self.error,
            "message": self.message
        }


class Hook:
    """钩子定义"""
    def __init__(
        self,
        hook_id: str,
        name: str,
        hook_type: HookType,
        enabled: bool = True,
        description: str = "",
        priority: int = 100,  # 优先级，数字越小越先执行
        conditions: Dict[str, Any] = None,  # 执行条件
        actions: List[str] = None,  # 关联的动作
        config: Dict[str, Any] = None  # 钩子配置
    ):
        self.hook_id = hook_id
        self.name = name
        self.hook_type = hook_type
        self.enabled = enabled
        self.description = description
        self.priority = priority
        self.conditions = conditions or {}
        self.actions = actions or []
        self.config = config or {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "hook_id": self.hook_id,
            "name": self.name,
            "hook_type": self.hook_type.value if isinstance(self.hook_type, HookType) else self.hook_type,
            "enabled": self.enabled,
            "description": self.description,
            "priority": self.priority,
            "conditions": self.conditions,
            "actions": self.actions,
            "config": self.config
        }


# ===== 内置钩子定义 =====

def create_security_filter_hook() -> Hook:
    """安全过滤钩子 - 过滤敏感内容"""
    return Hook(
        hook_id="security_filter",
        name="安全过滤",
        hook_type=HookType.PRE_MESSAGE,
        enabled=True,
        description="过滤消息中的敏感内容",
        priority=1,
        config={
            "blocked_patterns": [
                r"password[\s:=].+",
                r"api[_-]?key[\s:=].+",
                r"secret[\s:=].+",
                r"\b\d{15,18}\b",  # 身份证号
            ],
            "action": "block"  # 或 "mask"
        }
    )


def create_profanity_filter_hook() -> Hook:
    """脏话过滤钩子"""
    return Hook(
        hook_id="profanity_filter",
        name="脏话过滤",
        hook_type=HookType.PRE_MESSAGE,
        enabled=True,
        description="过滤消息中的不当语言",
        priority=2,
        config={
            "blocked_words": [],  # 可以配置自定义脏话列表
            "action": "mask"
        }
    )


def create_memory_hook() -> Hook:
    """记忆钩子 - 自动保存重要信息"""
    return Hook(
        hook_id="auto_memory",
        name="自动记忆",
        hook_type=HookType.POST_MESSAGE,
        enabled=True,
        description="自动保存重要信息到记忆",
        priority=50,
        conditions={
            "min_importance": 0.7
        }
    )


def create_conversation_summary_hook() -> Hook:
    """会话总结钩子"""
    return Hook(
        hook_id="conversation_summary",
        name="会话总结",
        hook_type=HookType.ON_SESSION_END,
        enabled=True,
        description="会话结束时生成总结",
        priority=100
    )


def create_tool_logger_hook() -> Hook:
    """工具日志钩子"""
    return Hook(
        hook_id="tool_logger",
        name="工具日志",
        hook_type=HookType.POST_TOOL_CALL,
        enabled=True,
        description="记录工具调用日志",
        priority=100
    )


# 内置钩子注册
BUILT_IN_HOOKS: Dict[str, Hook] = {
    "security_filter": create_security_filter_hook(),
    "profanity_filter": create_profanity_filter_hook(),
    "auto_memory": create_memory_hook(),
    "conversation_summary": create_conversation_summary_hook(),
    "tool_logger": create_tool_logger_hook(),
}


class HookManager:
    """钩子管理器"""
    
    def __init__(self):
        self.hooks: Dict[str, Hook] = BUILT_IN_HOOKS.copy()
        self._hook_handlers: Dict[str, List[Callable]] = {}
    
    def register_hook(self, hook: Hook):
        """注册钩子"""
        self.hooks[hook.hook_id] = hook
    
    def unregister_hook(self, hook_id: str) -> bool:
        """取消注册钩子"""
        if hook_id in self.hooks:
            del self.hooks[hook_id]
            return True
        return False
    
    def get_hook(self, hook_id: str) -> Optional[Hook]:
        """获取钩子"""
        return self.hooks.get(hook_id)
    
    def list_hooks(self, hook_type: HookType = None, enabled_only: bool = False) -> List[Hook]:
        """列出钩子"""
        result = list(self.hooks.values())
        
        if hook_type:
            result = [h for h in result if h.hook_type == hook_type]
        
        if enabled_only:
            result = [h for h in result if h.enabled]
        
        # 按优先级排序
        result.sort(key=lambda x: x.priority)
        
        return result
    
    def register_handler(self, hook_id: str, handler: Callable):
        """注册钩子处理器"""
        if hook_id not in self._hook_handlers:
            self._hook_handlers[hook_id] = []
        self._hook_handlers[hook_id].append(handler)
    
    async def execute_pre_message_hooks(
        self,
        message: str,
        context: Dict[str, Any] = None
    ) -> HookResult:
        """执行消息前置钩子"""
        hooks = self.list_hooks(HookType.PRE_MESSAGE, enabled_only=True)
        context = context or {}
        
        for hook in hooks:
            result = await self._execute_hook(hook, message, context)
            
            if not result.success:
                return result
            
            if result.modified and result.data:
                message = result.data
        
        return HookResult(success=True, data=message)
    
    async def execute_post_message_hooks(
        self,
        message: str,
        context: Dict[str, Any] = None
    ) -> HookResult:
        """执行消息后置钩子"""
        hooks = self.list_hooks(HookType.POST_MESSAGE, enabled_only=True)
        context = context or {}
        
        for hook in hooks:
            result = await self._execute_hook(hook, message, context)
            
            if not result.success:
                return result
        
        return HookResult(success=True, data=message)
    
    async def execute_pre_tool_call_hooks(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> HookResult:
        """执行工具调用前置钩子"""
        hooks = self.list_hooks(HookType.PRE_TOOL_CALL, enabled_only=True)
        context = context or {}
        
        for hook in hooks:
            result = await self._execute_hook(
                hook,
                {"tool_name": tool_name, "arguments": arguments},
                context
            )
            
            if not result.success:
                return result
            
            if result.modified and result.data:
                tool_name = result.data.get("tool_name", tool_name)
                arguments = result.data.get("arguments", arguments)
        
        return HookResult(success=True, data={"tool_name": tool_name, "arguments": arguments})
    
    async def execute_post_tool_call_hooks(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        result: Any,
        context: Dict[str, Any] = None
    ) -> HookResult:
        """执行工具调用后置钩子"""
        hooks = self.list_hooks(HookType.POST_TOOL_CALL, enabled_only=True)
        context = context or {}
        
        for hook in hooks:
            await self._execute_hook(
                hook,
                {"tool_name": tool_name, "arguments": arguments, "result": result},
                context
            )
        
        return HookResult(success=True)
    
    async def execute_error_hooks(
        self,
        error: Exception,
        context: Dict[str, Any] = None
    ) -> HookResult:
        """执行错误处理钩子"""
        hooks = self.list_hooks(HookType.ON_ERROR, enabled_only=True)
        context = context or {}
        
        error_info = {
            "error_type": type(error).__name__,
            "error_message": str(error)
        }
        
        for hook in hooks:
            await self._execute_hook(hook, error_info, context)
        
        return HookResult(success=True)
    
    async def execute_session_end_hooks(
        self,
        session_id: str,
        messages: List[Dict[str, Any]],
        context: Dict[str, Any] = None
    ) -> HookResult:
        """执行会话结束钩子"""
        hooks = self.list_hooks(HookType.ON_SESSION_END, enabled_only=True)
        context = context or {}
        
        for hook in hooks:
            await self._execute_hook(
                hook,
                {"session_id": session_id, "message_count": len(messages)},
                context
            )
        
        return HookResult(success=True)
    
    async def _execute_hook(self, hook: Hook, data: Any, context: Dict[str, Any]) -> HookResult:
        """执行单个钩子"""
        try:
            # 检查条件
            if not self._check_conditions(hook.conditions, data, context):
                return HookResult(success=True)
            
            # 执行内置钩子
            if hook.hook_id == "security_filter":
                return await self._security_filter_hook(hook, data)
            elif hook.hook_id == "profanity_filter":
                return await self._profanity_filter_hook(hook, data)
            elif hook.hook_id == "auto_memory":
                return await self._auto_memory_hook(hook, data, context)
            elif hook.hook_id == "tool_logger":
                return await self._tool_logger_hook(hook, data, context)
            
            # 执行自定义处理器
            if hook.hook_id in self._hook_handlers:
                for handler in self._hook_handlers[hook.hook_id]:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(data, context)
                    else:
                        handler(data, context)
            
            return HookResult(success=True)
            
        except Exception as e:
            return HookResult(success=False, error=str(e))
    
    def _check_conditions(
        self,
        conditions: Dict[str, Any],
        data: Any,
        context: Dict[str, Any]
    ) -> bool:
        """检查钩子执行条件"""
        if not conditions:
            return True
        
        # 检查数据类型
        if "data_type" in conditions:
            if isinstance(data, str) and conditions["data_type"] != "string":
                return False
            if isinstance(data, dict) and conditions["data_type"] != "object":
                return False
        
        # 检查最小重要性
        if "min_importance" in conditions:
            importance = context.get("importance", 1.0)
            if importance < conditions["min_importance"]:
                return False
        
        return True
    
    async def _security_filter_hook(self, hook: Hook, message: str) -> HookResult:
        """安全过滤钩子实现"""
        patterns = hook.config.get("blocked_patterns", [])
        action = hook.config.get("action", "mask")
        
        modified_message = message
        found_sensitive = False
        
        for pattern in patterns:
            matches = re.findall(pattern, modified_message, re.IGNORECASE)
            if matches:
                found_sensitive = True
                if action == "block":
                    return HookResult(
                        success=False,
                        error="消息包含敏感内容，已被阻止"
                    )
                elif action == "mask":
                    for match in matches:
                        modified_message = modified_message.replace(
                            match,
                            "[敏感内容]"
                        )
        
        return HookResult(
            success=True,
            modified=found_sensitive,
            data=modified_message
        )
    
    async def _profanity_filter_hook(self, hook: Hook, message: str) -> HookResult:
        """脏话过滤钩子实现"""
        # 这里可以使用更复杂的脏话词库
        blocked_words = hook.config.get("blocked_words", [])
        
        modified_message = message
        found_profanity = False
        
        for word in blocked_words:
            if word.lower() in modified_message.lower():
                modified_message = re.sub(
                    re.escape(word),
                    "*" * len(word),
                    modified_message,
                    flags=re.IGNORECASE
                )
                found_profanity = True
        
        return HookResult(
            success=True,
            modified=found_profanity,
            data=modified_message
        )
    
    async def _auto_memory_hook(
        self,
        hook: Hook,
        data: Any,
        context: Dict[str, Any]
    ) -> HookResult:
        """自动记忆钩子实现"""
        try:
            from .memory import add_session_memory
            
            session_id = context.get("session_id", "default")
            message = data if isinstance(data, str) else context.get("message", "")
            importance = context.get("importance", 0.5)
            
            # 根据配置决定是否保存
            if importance >= hook.conditions.get("min_importance", 0.7):
                add_session_memory(
                    session_id=session_id,
                    content=message,
                    importance=importance,
                    tags=["auto_saved"]
                )
            
            return HookResult(success=True)
            
        except Exception as e:
            return HookResult(success=False, error=str(e))
    
    async def _tool_logger_hook(
        self,
        hook: Hook,
        data: Any,
        context: Dict[str, Any]
    ) -> HookResult:
        """工具日志钩子实现"""
        import logging
        logger = logging.getLogger("agent.tools")
        
        tool_name = data.get("tool_name", "unknown")
        arguments = data.get("arguments", {})
        result = data.get("result", {})
        
        logger.info(
            f"Tool call: {tool_name} | "
            f"Args: {json.dumps(arguments, ensure_ascii=False)[:200]} | "
            f"Success: {'error' not in result}"
        )
        
        return HookResult(success=True)


# 导入 asyncio
import asyncio

# 全局钩子管理器
hook_manager = HookManager()


# ===== 便捷函数 =====

async def filter_message(message: str, context: Dict[str, Any] = None) -> str:
    """过滤消息"""
    result = await hook_manager.execute_pre_message_hooks(message, context)
    if result.success:
        return result.data or message
    return "[消息已被过滤]"


async def process_response(message: str, context: Dict[str, Any] = None) -> str:
    """处理响应"""
    result = await hook_manager.execute_post_message_hooks(message, context)
    if result.success:
        return result.data or message
    return message


def register_custom_hook(
    hook_id: str,
    name: str,
    hook_type: HookType,
    handler: Callable,
    description: str = "",
    priority: int = 100
) -> Hook:
    """注册自定义钩子"""
    hook = Hook(
        hook_id=hook_id,
        name=name,
        hook_type=hook_type,
        description=description,
        priority=priority
    )
    hook_manager.register_hook(hook)
    hook_manager.register_handler(hook_id, handler)
    return hook


def list_available_hooks(hook_type: HookType = None) -> List[Dict[str, Any]]:
    """列出可用钩子"""
    hooks = hook_manager.list_hooks(hook_type)
    return [h.to_dict() for h in hooks]
