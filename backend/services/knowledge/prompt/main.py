"""Prompt 版本管理服务 (P3-004) - 支持 Prompt 模板存储、版本控制、A/B 测试"""

import uuid
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import json
import os

router = APIRouter(prefix="/prompt", tags=["Prompt Management"])

# SQLAlchemy
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from common.database.postgresql import Base, AsyncSessionLocal
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession


# ==================== 数据库模型 ====================
class PromptTemplate(Base):
    """Prompt 模板"""
    __tablename__ = "prompt_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, index=True, nullable=False)  # 模板名称（唯一标识）
    version = Column(String(20), default="v1.0.0")  # 版本号
    content = Column(Text, nullable=False)  # Prompt 内容
    system_prompt = Column(Text)  # 系统提示词
    description = Column(Text)  # 描述
    variables = Column(JSON)  # 变量定义 [{"name": "query", "type": "string", "required": true}]
    metadata_json = Column("metadata", JSON)  # 元数据（使用 metadata_json 避免与 MetaData 冲突）
    is_active = Column(Boolean, default=True)  # 是否激活
    is_default = Column(Boolean, default=False)  # 是否为默认版本
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))  # 创建者


class PromptVersion(Base):
    """Prompt 版本历史"""
    __tablename__ = "prompt_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id = Column(UUID(as_uuid=True), ForeignKey("prompt_templates.id"), nullable=False)
    version = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    system_prompt = Column(Text)
    change_log = Column(Text)  # 变更说明
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))


class PromptExperiment(Base):
    """Prompt A/B 测试实验"""
    __tablename__ = "prompt_experiments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, index=True)  # 实验名称
    template_a_id = Column(UUID(as_uuid=True), ForeignKey("prompt_templates.id"))  # A 版本
    template_b_id = Column(UUID(as_uuid=True), ForeignKey("prompt_templates.id"))  # B 版本
    traffic_split = Column(Integer, default=50)  # B 版本流量占比 (0-100)
    status = Column(String(20), default="running")  # running, paused, stopped
    metrics = Column(JSON)  # 实验指标 {"version_a_wins": 10, "version_b_wins": 15}
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    ended_at = Column(DateTime)


# ==================== 数据结构 ====================
class PromptTemplateCreate(BaseModel):
    """创建 Prompt 模板"""
    name: str
    version: str = "v1.0.0"
    content: str
    system_prompt: Optional[str] = None
    description: Optional[str] = None
    variables: Optional[List[Dict[str, Any]]] = None
    metadata_json: Optional[Dict[str, Any]] = None
    is_default: bool = True


class PromptTemplateUpdate(BaseModel):
    """更新 Prompt 模板"""
    content: Optional[str] = None
    system_prompt: Optional[str] = None
    description: Optional[str] = None
    variables: Optional[List[Dict[str, Any]]] = None
    metadata_json: Optional[Dict[str, Any]] = None


class PromptTemplateResponse(BaseModel):
    """Prompt 模板响应"""
    id: str
    name: str
    version: str
    content: str
    system_prompt: Optional[str]
    description: Optional[str]
    variables: Optional[List[Dict[str, Any]]]
    metadata_json: Optional[Dict[str, Any]]
    is_active: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PromptRenderRequest(BaseModel):
    """渲染 Prompt 请求"""
    template_name: str
    variables: Dict[str, Any]
    version: Optional[str] = None  # 指定版本，不指定则使用默认激活版本


class PromptRenderResponse(BaseModel):
    """渲染 Prompt 响应"""
    template_name: str
    version: str
    prompt: str
    system_prompt: Optional[str]
    variables_used: List[str]


# ==================== Prompt 管理器 ====================
class PromptManager:
    """Prompt 管理器 - 单例"""

    _instance = None
    _cache: Dict[str, PromptTemplateResponse] = {}
    _cache_time: Dict[str, datetime] = {}
    _cache_ttl = 60  # 缓存 TTL 60 秒

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def get_template(self, name: str, version: Optional[str] = None) -> Optional[PromptTemplateResponse]:
        """获取 Prompt 模板"""
        # 尝试缓存
        cache_key = f"{name}:{version or 'default'}"
        if cache_key in self._cache:
            cache_age = (datetime.utcnow() - self._cache_time[cache_key]).total_seconds()
            if cache_age < self._cache_ttl:
                return self._cache[cache_key]

        # 数据库查询
        async with AsyncSessionLocal() as session:
            query = select(PromptTemplate).where(
                PromptTemplate.name == name,
                PromptTemplate.is_active == True
            )
            if version:
                query = query.where(PromptTemplate.version == version)
            else:
                query = query.where(PromptTemplate.is_default == True)

            result = await session.execute(query)
            template = result.scalar_one_or_none()

            if template:
                response = PromptTemplateResponse(
                    id=str(template.id),
                    name=template.name,
                    version=template.version,
                    content=template.content,
                    system_prompt=template.system_prompt,
                    description=template.description,
                    variables=template.variables,
                    metadata_json=template.metadata_json,
                    is_active=template.is_active,
                    is_default=template.is_default,
                    created_at=template.created_at,
                    updated_at=template.updated_at
                )
                # 更新缓存
                self._cache[cache_key] = response
                self._cache_time[cache_key] = datetime.utcnow()
                return response

        return None

    async def render(self, template_name: str, variables: Dict[str, Any], version: Optional[str] = None) -> Optional[PromptRenderResponse]:
        """渲染 Prompt"""
        template = await self.get_template(template_name, version)
        if not template:
            return None

        # 渲染模板
        try:
            prompt = template.content
            for key, value in variables.items():
                prompt = prompt.replace(f"{{{{{key}}}}}", str(value))

            system_prompt = template.system_prompt
            if system_prompt:
                for key, value in variables.items():
                    system_prompt = system_prompt.replace(f"{{{{{key}}}}}", str(value))

            return PromptRenderResponse(
                template_name=template_name,
                version=template.version,
                prompt=prompt,
                system_prompt=system_prompt,
                variables_used=list(variables.keys())
            )
        except Exception as e:
            print(f"Prompt 渲染失败：{e}")
            return None

    async def create_version(self, template_id: uuid.UUID, version: str, content: str, system_prompt: Optional[str], change_log: str, created_by: Optional[str] = None) -> PromptTemplate:
        """创建新版本"""
        async with AsyncSessionLocal() as session:
            # 查询原模板
            result = await session.execute(
                select(PromptTemplate).where(PromptTemplate.id == template_id)
            )
            old_template = result.scalar_one_or_none()
            if not old_template:
                raise HTTPException(status_code=404, detail="模板不存在")

            # 创建新模板（新版本）
            new_template = PromptTemplate(
                name=old_template.name,
                version=version,
                content=content,
                system_prompt=system_prompt or old_template.system_prompt,
                description=old_template.description,
                variables=old_template.variables,
                metadata_json=old_template.metadata_json,
                is_active=True,
                is_default=False,  # 新版本默认不激活
                created_by=created_by
            )
            session.add(new_template)

            # 创建版本历史
            version_history = PromptVersion(
                template_id=template_id,
                version=version,
                content=content,
                system_prompt=system_prompt or old_template.system_prompt,
                change_log=change_log,
                created_by=created_by
            )
            session.add(version_history)

            await session.commit()
            await session.refresh(new_template)
            return new_template

    async def set_default_version(self, name: str, version: str) -> bool:
        """设置默认版本"""
        async with AsyncSessionLocal() as session:
            # 取消当前默认版本
            await session.execute(
                PromptTemplate.update()
                .where(PromptTemplate.name == name, PromptTemplate.is_default == True)
                .values(is_default=False)
            )

            # 设置新默认版本
            await session.execute(
                PromptTemplate.update()
                .where(PromptTemplate.name == name, PromptTemplate.version == version)
                .values(is_default=True)
            )

            await session.commit()

            # 清除缓存
            self._cache = {k: v for k, v in self._cache.items() if not k.startswith(f"{name}:")}

            return True

    def clear_cache(self, name: Optional[str] = None):
        """清除缓存"""
        if name:
            self._cache = {k: v for k, v in self._cache.items() if not k.startswith(f"{name}:")}
            self._cache_time = {k: v for k, v in self._cache_time.items() if not k.startswith(f"{name}:")}
        else:
            self._cache.clear()
            self._cache_time.clear()


# 全局 Prompt 管理器
prompt_manager = PromptManager()


# ==================== API 接口 ====================
@router.post("/templates", response_model=Dict)
async def create_template(template: PromptTemplateCreate):
    """创建 Prompt 模板"""
    async with AsyncSessionLocal() as session:
        # 如果设置为默认版本，取消其他默认版本
        if template.is_default:
            await session.execute(
                PromptTemplate.update()
                .where(PromptTemplate.name == template.name, PromptTemplate.is_default == True)
                .values(is_default=False)
            )

        new_template = PromptTemplate(
            name=template.name,
            version=template.version,
            content=template.content,
            system_prompt=template.system_prompt,
            description=template.description,
            variables=template.variables,
            metadata_json=template.metadata_json,
            is_active=True,
            is_default=template.is_default
        )
        session.add(new_template)
        await session.commit()
        await session.refresh(new_template)

        # 清除缓存
        prompt_manager.clear_cache(template.name)

        return {
            "code": 200,
            "message": "创建成功",
            "data": {
                "id": str(new_template.id),
                "name": new_template.name,
                "version": new_template.version
            }
        }


@router.get("/templates/{name}", response_model=Dict)
async def get_template(name: str, version: Optional[str] = Query(None)):
    """获取 Prompt 模板"""
    template = await prompt_manager.get_template(name, version)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    return {
        "code": 200,
        "data": template
    }


@router.get("/templates", response_model=Dict)
async def list_templates(name: Optional[str] = Query(None)):
    """获取 Prompt 模板列表"""
    async with AsyncSessionLocal() as session:
        query = select(PromptTemplate).where(PromptTemplate.is_active == True)
        if name:
            query = query.where(PromptTemplate.name == name)
        query = query.order_by(PromptTemplate.created_at.desc())

        result = await session.execute(query)
        templates = result.scalars().all()

        return {
            "code": 200,
            "data": {
                "templates": [
                    {
                        "id": str(t.id),
                        "name": t.name,
                        "version": t.version,
                        "description": t.description,
                        "is_default": t.is_default,
                        "created_at": t.created_at.isoformat()
                    }
                    for t in templates
                ]
            }
        }


@router.put("/templates/{name}", response_model=Dict)
async def update_template(name: str, update: PromptTemplateUpdate):
    """更新 Prompt 模板（创建新版本）"""
    # 获取当前模板
    template = await prompt_manager.get_template(name)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    # 解析版本号
    version_parts = template.version.split('.')
    try:
        major = int(version_parts[0].replace('v', ''))
        minor = int(version_parts[1])
        patch = int(version_parts[2])
        new_version = f"v{major}.{minor}.{patch + 1}"
    except:
        new_version = f"v{major}.{int(version_parts[1]) + 1}.0" if len(version_parts) > 1 else "v1.1.0"

    # 创建新版本
    new_template = await prompt_manager.create_version(
        template_id=uuid.UUID(template.id),
        version=new_version,
        content=update.content or template.content,
        system_prompt=update.system_prompt or template.system_prompt,
        change_log=f"更新版本到 {new_version}"
    )

    return {
        "code": 200,
        "message": f"创建新版本 {new_version}",
        "data": {
            "id": str(new_template.id),
            "version": new_version
        }
    }


@router.post("/templates/{name}/activate", response_model=Dict)
async def activate_template(name: str, version: str = Query(...)):
    """激活指定版本（设为默认）"""
    await prompt_manager.set_default_version(name, version)
    return {
        "code": 200,
        "message": f"已激活 {name} 的 {version} 版本"
    }


@router.delete("/templates/{name}", response_model=Dict)
async def deactivate_template(name: str):
    """停用 Prompt 模板"""
    async with AsyncSessionLocal() as session:
        await session.execute(
            PromptTemplate.update()
            .where(PromptTemplate.name == name)
            .values(is_active=False)
        )
        await session.commit()

        prompt_manager.clear_cache(name)

        return {"code": 200, "message": "模板已停用"}


@router.post("/render", response_model=Dict)
async def render_prompt(request: PromptRenderRequest):
    """渲染 Prompt"""
    result = await prompt_manager.render(
        template_name=request.template_name,
        variables=request.variables,
        version=request.version
    )

    if not result:
        raise HTTPException(status_code=404, detail="模板不存在或渲染失败")

    return {
        "code": 200,
        "data": {
            "template_name": result.template_name,
            "version": result.version,
            "prompt": result.prompt,
            "system_prompt": result.system_prompt,
            "variables_used": result.variables_used
        }
    }


@router.get("/versions/{name}", response_model=Dict)
async def list_versions(name: str):
    """获取模板的所有版本"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(PromptTemplate)
            .where(PromptTemplate.name == name)
            .order_by(PromptTemplate.created_at.desc())
        )
        templates = result.scalars().all()

        return {
            "code": 200,
            "data": {
                "versions": [
                    {
                        "version": t.version,
                        "is_default": t.is_default,
                        "created_at": t.created_at.isoformat(),
                        "description": t.description
                    }
                    for t in templates
                ]
            }
        }


@router.get("/history/{template_id}", response_model=Dict)
async def get_version_history(template_id: str):
    """获取版本历史"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(PromptVersion)
            .where(PromptVersion.template_id == uuid.UUID(template_id))
            .order_by(PromptVersion.created_at.desc())
        )
        versions = result.scalars().all()

        return {
            "code": 200,
            "data": {
                "history": [
                    {
                        "version": v.version,
                        "change_log": v.change_log,
                        "created_at": v.created_at.isoformat(),
                        "created_by": v.created_by
                    }
                    for v in versions
                ]
            }
        }


# ==================== 预定义 Prompt 模板 ====================
async def init_default_prompts():
    """初始化默认 Prompt 模板"""
    async with AsyncSessionLocal() as session:
        # 检查是否已存在
        result = await session.execute(
            select(PromptTemplate).where(PromptTemplate.name == "rag_default")
        )
        if result.scalar_one_or_none():
            return  # 已存在

        # RAG 默认模板
        default_rag = PromptTemplate(
            name="rag_default",
            version="v1.0.0",
            content="""你是一个智能教学助手。根据以下参考知识回答学生问题。

## 参考知识
{{context}}

## 学生问题
{{query}}

## 要求
1. 用中文回答，简洁准确
2. 基于参考知识回答，不要编造
3. 如果参考知识不足，请说明
4. 适当鼓励学生""",
            system_prompt="你是一位专业的编程教师，擅长用简洁易懂的语言解释编程概念。",
            description="RAG 默认模板",
            variables=[
                {"name": "context", "type": "string", "required": True, "description": "参考知识"},
                {"name": "query", "type": "string", "required": True, "description": "学生问题"}
            ],
            is_active=True,
            is_default=True
        )
        session.add(default_rag)

        # RAG 详细模板
        detailed_rag = PromptTemplate(
            name="rag_detailed",
            version="v1.0.0",
            content="""你是一位经验丰富的{{subject}}教师。请根据以下参考资料回答学生的问题。

## 参考资料
{% for doc in context_docs %}
【资料{{loop.index}}】(来源：{{doc.channel}}, 相关度：{{doc.score}})
{{doc.content}}
{% endfor %}

## 学生问题
{{query}}

## 回答要求
1. **准确性**: 基于参考资料，不编造未知信息
2. **完整性**: 覆盖问题的关键方面
3. **易懂性**: 使用简洁易懂的语言
4. **结构性**: 分点阐述，逻辑清晰
5. **鼓励性**: 适当给予学习建议和鼓励

{% if student_level %}
## 学生水平
{{student_level}}
请根据学生水平调整回答的深度和表达方式。
{% endif %}

## 回答""",
            system_prompt="你是一位专业、耐心、细致的{{subject}}教师，擅长用生活中的例子帮助学生理解抽象概念。",
            description="RAG 详细模板 - 支持多文档和学生水平",
            variables=[
                {"name": "subject", "type": "string", "required": True, "description": "科目"},
                {"name": "context_docs", "type": "array", "required": True, "description": "参考文档列表"},
                {"name": "query", "type": "string", "required": True, "description": "学生问题"},
                {"name": "student_level", "type": "string", "required": False, "description": "学生水平（beginner/intermediate/advanced）"}
            ],
            is_active=True,
            is_default=False
        )
        session.add(detailed_rag)

        # 代码解释模板
        code_explanation = PromptTemplate(
            name="code_explanation",
            version="v1.0.0",
            content="""你是一位编程教学专家。请解释以下代码并回答学生的问题。

## 代码
```{{language}}
{{code}}
```

## 学生问题
{{query}}

## 回答结构
1. **代码功能**: 简要说明代码的作用
2. **关键概念**: 解释涉及的核心概念
3. **代码解析**: 逐行或逐块解释代码逻辑
4. **运行示例**: 给出示例输入输出（如适用）
5. **常见问题**: 提醒可能的错误和注意事项

请用通俗易懂的语言，适当使用生活中的类比。""",
            system_prompt="你是一位幽默风趣的编程教师，擅长用生活中的例子解释编程概念。",
            description="代码解释专用模板",
            variables=[
                {"name": "language", "type": "string", "required": True, "description": "编程语言"},
                {"name": "code", "type": "string", "required": True, "description": "代码内容"},
                {"name": "query", "type": "string", "required": True, "description": "学生问题"}
            ],
            is_active=True,
            is_default=False
        )
        session.add(code_explanation)

        await session.commit()
        print("[Prompt] 默认 Prompt 模板初始化完成")


# 自动初始化默认模板
# 注意：实际使用时需要在 startup 事件中调用
