"""Agent 类型定义和枚举 - 参照 Claude Code Agent 设计"""
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class AgentType(str, Enum):
    """Agent 类型枚举"""
    GENERAL = "general"           # 通用代理 - 处理各种任务
    EXPLORER = "explorer"         # 探索代理 - 代码搜索和分析
    PLANNER = "planner"           # 计划代理 - 软件架构和规划
    VERIFIER = "verifier"         # 验证代理 - 验证实现是否符合要求
    TUTOR = "tutor"               # 辅导代理 - 教学答疑
    GRADER = "grader"             # 批改代理 - 作业批改
    CUSTOM = "custom"             # 自定义代理


class EffortLevel(str, Enum):
    """任务努力级别"""
    LOW = "low"           # 快速回答
    MEDIUM = "medium"     # 中等深度
    HIGH = "high"         # 深入分析
    MAX = "max"           # 全面分析


class PermissionMode(str, Enum):
    """权限模式"""
    ASK = "ask"           # 每次询问
    AUTO = "auto"         # 自动执行
    BYPASS = "bypass"      # 绕过限制


class MemoryScope(str, Enum):
    """记忆范围"""
    SESSION = "session"   # 会话级别
    AGENT = "agent"       # Agent 持久化
    USER = "user"         # 用户级别
    PROJECT = "project"   # 项目级别


class AgentDefinition(BaseModel):
    """Agent 完整定义"""
    # 基本信息
    id: str
    name: str
    agent_type: AgentType = AgentType.GENERAL
    when_to_use: str = ""
    when_not_to_use: str = ""
    
    # Prompt 配置
    prompt: str = ""
    system_prompt_template: Optional[str] = None  # 可选的模板 ID
    
    # 工具配置
    enabled_tools: List[str] = Field(default_factory=list)
    disallowed_tools: List[str] = Field(default_factory=list)
    max_tool_calls: int = 10
    
    # 运行配置
    effort: EffortLevel = EffortLevel.MEDIUM
    permission_mode: PermissionMode = PermissionMode.ASK
    max_turns: int = 20
    background: bool = False
    
    # 内存配置
    memory_scope: MemoryScope = MemoryScope.SESSION
    memory_enabled: bool = True
    
    # 调用配置
    callable_by_others: bool = False
    english_id: str = ""
    
    # 元数据
    avatar: Optional[str] = None
    color: Optional[str] = None  # UI 颜色
    model: Optional[str] = None  # 指定模型
    temperature: float = 1.0
    max_tokens: int = 4096
    
    # 钩子配置
    pre_hooks: List[str] = Field(default_factory=list)  # 前置钩子
    post_hooks: List[str] = Field(default_factory=list)  # 后置钩子
    
    # 技能预加载
    skills: List[str] = Field(default_factory=list)
    
    # 时间戳
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    class Config:
        use_enum_values = True


class AgentCapability(BaseModel):
    """Agent 能力描述"""
    agent_type: AgentType
    description: str
    strengths: List[str]
    weaknesses: List[str]
    recommended_tools: List[str]
    example_tasks: List[str]


# 内置 Agent 能力定义
BUILT_IN_AGENT_CAPABILITIES = {
    AgentType.GENERAL: AgentCapability(
        agent_type=AgentType.GENERAL,
        description="通用任务处理代理",
        strengths=[
            "处理多种类型的用户请求",
            "灵活使用各种工具完成任务",
            "提供综合性的解决方案"
        ],
        weaknesses=[
            "可能不如专门代理深入"
        ],
        recommended_tools=["reading", "editing", "terminal", "tavily_search", "knowledge_search"],
        example_tasks=[
            "回答各种问题",
            "帮助用户完成学习任务",
            "跨领域知识查询"
        ]
    ),
    AgentType.EXPLORER: AgentCapability(
        agent_type=AgentType.EXPLORER,
        description="代码探索和搜索代理",
        strengths=[
            "在大规模代码库中搜索",
            "分析多个文件的相关内容",
            "调查复杂问题",
            "多步骤研究任务"
        ],
        weaknesses=[
            "只读模式，不修改代码",
            "不适合直接执行任务"
        ],
        recommended_tools=["reading", "tavily_search", "knowledge_search"],
        example_tasks=[
            "查找特定功能的实现位置",
            "分析代码结构和依赖",
            "搜索相关的代码片段",
            "理解代码逻辑"
        ]
    ),
    AgentType.PLANNER: AgentCapability(
        agent_type=AgentType.PLANNER,
        description="软件架构和计划代理",
        strengths=[
            "理解需求并设计解决方案",
            "分析现有代码结构",
            "制定详细的实现计划",
            "提供架构建议"
        ],
        weaknesses=[
            "只提供计划，不直接实现",
            "需要用户提供详细需求"
        ],
        recommended_tools=["reading", "tavily_search", "knowledge_search"],
        example_tasks=[
            "设计系统架构",
            "制定开发计划",
            "分析技术选型",
            "提供代码重构建议"
        ]
    ),
    AgentType.VERIFIER: AgentCapability(
        agent_type=AgentType.VERIFIER,
        description="实现验证代理",
        strengths=[
            "验证实现是否符合需求",
            "检查代码质量和规范",
            "测试功能正确性",
            "提供改进建议"
        ],
        weaknesses=[
            "需要具体的验证标准",
            "可能产生误报"
        ],
        recommended_tools=["reading", "terminal", "knowledge_search"],
        example_tasks=[
            "验证作业完成度",
            "检查代码规范",
            "测试功能是否正确",
            "评估实现质量"
        ]
    ),
    AgentType.TUTOR: AgentCapability(
        agent_type=AgentType.TUTOR,
        description="智能辅导代理",
        strengths=[
            "解释复杂概念",
            "因材施教",
            "提供学习建议",
            "回答学科问题"
        ],
        weaknesses=[
            "不适合执行操作任务",
            "可能需要外部资源"
        ],
        recommended_tools=["tavily_search", "knowledge_search", "preview"],
        example_tasks=[
            "解答学习问题",
            "解释知识点",
            "提供学习指导",
            "推荐学习资源"
        ]
    ),
    AgentType.GRADER: AgentCapability(
        agent_type=AgentType.GRADER,
        description="作业批改代理",
        strengths=[
            "自动批改作业",
            "提供详细反馈",
            "识别常见错误",
            "评分和建议"
        ],
        weaknesses=[
            "需要明确的评分标准",
            "复杂题目可能需要人工"
        ],
        recommended_tools=["reading", "editing", "knowledge_search"],
        example_tasks=[
            "批改选择题",
            "批改编程作业",
            "检查作业完成度",
            "提供改进建议"
        ]
    )
}
