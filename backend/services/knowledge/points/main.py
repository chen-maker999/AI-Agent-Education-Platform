"""Knowledge point management service - PostgreSQL storage."""

import uuid
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, status, Query, Depends
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import select, func, or_
from common.models.response import ResponseModel
from common.database.postgresql import Base, AsyncSessionLocal

router = APIRouter(prefix="/knowledge/points", tags=["Knowledge Points"])


# SQLAlchemy Model
class KnowledgePoint(Base):
    __tablename__ = "knowledge_points"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    point_id = Column(String(100), unique=True, index=True)
    course_id = Column(String(100), index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    parent_id = Column(String(100), index=True)
    level = Column(Integer, default=1)
    sort_order = Column(Integer, default=0)
    status = Column(String(20), default="active")
    meta_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Pydantic models
class KnowledgePointCreate(BaseModel):
    course_id: str
    name: str
    code: str
    description: Optional[str] = ""
    parent_id: Optional[str] = None
    level: int = 1
    sort_order: int = 0
    meta_data: dict = {}


class KnowledgePointUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None
    meta_data: Optional[dict] = None


# Initialize database table
async def init_knowledge_db():
    """Initialize knowledge points database table."""
    from sqlalchemy import text
    async with AsyncSessionLocal() as conn:
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS knowledge_points (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                point_id VARCHAR(100) UNIQUE,
                course_id VARCHAR(100),
                name VARCHAR(255) NOT NULL,
                code VARCHAR(100) NOT NULL,
                description TEXT,
                parent_id VARCHAR(100),
                level INTEGER DEFAULT 1,
                sort_order INTEGER DEFAULT 0,
                status VARCHAR(20) DEFAULT 'active',
                meta_data JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        await conn.commit()


# Seed initial knowledge points
async def seed_knowledge_points():
    """Seed initial knowledge points if empty."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(func.count(KnowledgePoint.id)))
        count = result.scalar() or 0
        
        if count == 0:
            # Create sample knowledge points
            sample_points = [
                {"name": "Python基础", "code": "PY001", "course_id": "python", "level": 1, "description": "Python编程基础知识点"},
                {"name": "变量和数据类型", "code": "PY001-01", "course_id": "python", "parent_code": "PY001", "level": 2, "description": "Python中的变量和数据类型"},
                {"name": "运算符", "code": "PY001-02", "course_id": "python", "parent_code": "PY001", "level": 2, "description": "Python运算符"},
                {"name": "控制流", "code": "PY001-03", "course_id": "python", "parent_code": "PY001", "level": 2, "description": "条件语句和循环"},
                {"name": "数据结构", "code": "PY002", "course_id": "python", "level": 1, "description": "Python数据结构"},
                {"name": "列表", "code": "PY002-01", "course_id": "python", "parent_code": "PY002", "level": 2, "description": "Python列表操作"},
                {"name": "字典", "code": "PY002-02", "course_id": "python", "parent_code": "PY002", "level": 2, "description": "Python字典操作"},
                {"name": "函数", "code": "PY003", "course_id": "python", "level": 1, "description": "Python函数定义和使用"},
            ]
            
            point_id_map = {}
            for p in sample_points:
                parent_id = point_id_map.get(p.get("parent_code"))
                point = KnowledgePoint(
                    point_id=str(uuid.uuid4())[:8],
                    course_id=p["course_id"],
                    name=p["name"],
                    code=p["code"],
                    description=p.get("description", ""),
                    parent_id=parent_id,
                    level=p["level"],
                    sort_order=p.get("sort_order", 0),
                    status="active",
                    meta_data={"importance": "high"}
                )
                session.add(point)
                point_id_map[p["code"]] = point.point_id
            
            await session.commit()


# Try to initialize on import
try:
    import asyncio
    asyncio.create_task(init_knowledge_db())
    asyncio.create_task(seed_knowledge_points())
except:
    pass


@router.post("", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
async def create_knowledge_point(data: KnowledgePointCreate):
    """Create knowledge point."""
    async with AsyncSessionLocal() as session:
        # Check for duplicate code
        result = await session.execute(
            select(KnowledgePoint).where(KnowledgePoint.code == data.code)
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="知识点代码已存在")
        
        point = KnowledgePoint(
            point_id=str(uuid.uuid4())[:8],
            course_id=data.course_id,
            name=data.name,
            code=data.code,
            description=data.description or "",
            parent_id=data.parent_id,
            level=data.level,
            sort_order=data.sort_order,
            status="active",
            meta_data=data.meta_data
        )
        session.add(point)
        await session.commit()
        await session.refresh(point)
        
        return ResponseModel(code=200, message="success", data={
            "id": str(point.id),
            "point_id": point.point_id,
            "course_id": point.course_id,
            "name": point.name,
            "code": point.code,
            "description": point.description,
            "parent_id": point.parent_id,
            "level": point.level,
            "sort_order": point.sort_order,
            "status": point.status,
            "meta_data": point.meta_data,
            "created_at": point.created_at.isoformat() if point.created_at else None,
            "updated_at": point.updated_at.isoformat() if point.updated_at else None,
        })


@router.get("/{point_id}", response_model=ResponseModel)
async def get_knowledge_point(point_id: str):
    """Get knowledge point by ID."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(KnowledgePoint).where(
                or_(KnowledgePoint.id == point_id, KnowledgePoint.point_id == point_id)
            )
        )
        point = result.scalar_one_or_none()
        if not point:
            raise HTTPException(status_code=404, detail="Knowledge point not found")
        
        return ResponseModel(code=200, message="success", data={
            "id": str(point.id),
            "point_id": point.point_id,
            "course_id": point.course_id,
            "name": point.name,
            "code": point.code,
            "description": point.description,
            "parent_id": point.parent_id,
            "level": point.level,
            "sort_order": point.sort_order,
            "status": point.status,
            "meta_data": point.meta_data,
            "created_at": point.created_at.isoformat() if point.created_at else None,
            "updated_at": point.updated_at.isoformat() if point.updated_at else None,
        })


@router.put("/{point_id}", response_model=ResponseModel)
async def update_knowledge_point(point_id: str, data: KnowledgePointUpdate):
    """Update knowledge point."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(KnowledgePoint).where(
                or_(KnowledgePoint.id == point_id, KnowledgePoint.point_id == point_id)
            )
        )
        point = result.scalar_one_or_none()
        if not point:
            raise HTTPException(status_code=404, detail="Knowledge point not found")
        
        if data.name is not None:
            point.name = data.name
        if data.description is not None:
            point.description = data.description
        if data.sort_order is not None:
            point.sort_order = data.sort_order
        if data.meta_data is not None:
            point.meta_data = data.meta_data
        
        point.updated_at = datetime.utcnow()
        await session.commit()
        await session.refresh(point)
        
        return ResponseModel(code=200, message="success", data={
            "id": str(point.id),
            "point_id": point.point_id,
            "name": point.name,
            "description": point.description,
            "sort_order": point.sort_order,
            "meta_data": point.meta_data,
            "updated_at": point.updated_at.isoformat() if point.updated_at else None,
        })


@router.delete("/{point_id}", response_model=ResponseModel)
async def delete_knowledge_point(point_id: str):
    """Delete knowledge point."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(KnowledgePoint).where(
                or_(KnowledgePoint.id == point_id, KnowledgePoint.point_id == point_id)
            )
        )
        point = result.scalar_one_or_none()
        if not point:
            raise HTTPException(status_code=404, detail="Knowledge point not found")
        
        await session.delete(point)
        await session.commit()
        
        return ResponseModel(code=200, message="删除成功")


@router.get("", response_model=ResponseModel)
async def list_knowledge_points(
    course_id: str = Query(None),
    parent_id: str = Query(None),
    status: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """List knowledge points with pagination."""
    async with AsyncSessionLocal() as session:
        query = select(KnowledgePoint)
        
        if course_id:
            query = query.where(KnowledgePoint.course_id == course_id)
        if parent_id:
            query = query.where(KnowledgePoint.parent_id == parent_id)
        if status:
            query = query.where(KnowledgePoint.status == status)
        
        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await session.execute(count_query)
        total = total_result.scalar() or 0
        
        # Get paginated results
        query = query.order_by(KnowledgePoint.sort_order, KnowledgePoint.code)
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await session.execute(query)
        points = result.scalars().all()
        
        items = [{
            "id": str(p.id),
            "point_id": p.point_id,
            "course_id": p.course_id,
            "name": p.name,
            "code": p.code,
            "description": p.description,
            "parent_id": p.parent_id,
            "level": p.level,
            "sort_order": p.sort_order,
            "status": p.status,
            "meta_data": p.meta_data,
        } for p in points]
        
        return ResponseModel(code=200, message="success", data={
            "items": items, 
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        })


@router.get("/{point_id}/children", response_model=ResponseModel)
async def get_children(point_id: str):
    """Get child knowledge points."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(KnowledgePoint).where(KnowledgePoint.parent_id == point_id)
        )
        children = result.scalars().all()
        
        items = [{
            "id": str(p.id),
            "point_id": p.point_id,
            "name": p.name,
            "code": p.code,
            "level": p.level,
            "status": p.status,
        } for p in children]
        
        return ResponseModel(code=200, message="success", data=items)


@router.get("/{point_id}/tree", response_model=ResponseModel)
async def get_knowledge_tree(point_id: str):
    """Get knowledge tree from point."""
    async with AsyncSessionLocal() as session:
        # Get root point
        result = await session.execute(
            select(KnowledgePoint).where(
                or_(KnowledgePoint.id == point_id, KnowledgePoint.point_id == point_id)
            )
        )
        root = result.scalar_one_or_none()
        if not root:
            raise HTTPException(status_code=404, detail="Knowledge point not found")
        
        # Build tree recursively
        async def build_tree(pid: str) -> dict:
            result = await session.execute(
                select(KnowledgePoint).where(KnowledgePoint.parent_id == pid)
            )
            children = result.scalars().all()
            
            return {
                "id": str(root.id) if pid == point_id else pid,
                "point_id": root.point_id if pid == point_id else pid,
                "name": root.name if pid == point_id else "",
                "children": [await build_tree(c.point_id) for c in children]
            }
        
        tree = await build_tree(root.point_id)
        return ResponseModel(code=200, message="success", data=tree)


@router.get("/courses/{course_id}/tree", response_model=ResponseModel)
async def get_course_tree(course_id: str):
    """Get knowledge tree for a course."""
    async with AsyncSessionLocal() as session:
        # Get root points (level 1)
        result = await session.execute(
            select(KnowledgePoint).where(
                KnowledgePoint.course_id == course_id,
                KnowledgePoint.level == 1
            ).order_by(KnowledgePoint.sort_order, KnowledgePoint.code)
        )
        root_points = result.scalars().all()
        
        async def build_tree(point: KnowledgePoint) -> dict:
            child_result = await session.execute(
                select(KnowledgePoint).where(KnowledgePoint.parent_id == point.point_id)
            )
            children = child_result.scalars().all()
            
            return {
                "id": str(point.id),
                "point_id": point.point_id,
                "name": point.name,
                "code": point.code,
                "level": point.level,
                "description": point.description,
                "children": [await build_tree(c) for c in children]
            }
        
        tree = [await build_tree(p) for p in root_points]
        
        return ResponseModel(code=200, message="success", data={
            "course_id": course_id,
            "knowledge_tree": tree
        })


@router.get("/schema", response_model=ResponseModel)
async def get_schema():
    """Get knowledge point schema."""
    return ResponseModel(
        code=200,
        message="success",
        data={
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "KnowledgePoint",
            "type": "object",
            "required": ["name", "code", "course_id"],
            "properties": {
                "course_id": {"type": "string", "description": "课程ID"},
                "name": {"type": "string", "description": "知识点名称"},
                "code": {"type": "string", "description": "知识点编码"},
                "description": {"type": "string", "description": "知识点描述"},
                "parent_id": {"type": "string", "description": "父知识点ID"},
                "level": {"type": "integer", "description": "知识点层级"},
                "sort_order": {"type": "integer", "description": "排序顺序"},
                "meta_data": {"type": "object", "description": "扩展元数据"}
            }
        }
    )
