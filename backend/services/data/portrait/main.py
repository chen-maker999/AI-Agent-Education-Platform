"""Student Portrait service - Real PostgreSQL storage."""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from common.models.response import ResponseModel
from common.database.postgresql import Base, AsyncSessionLocal
import json

router = APIRouter(prefix="/portrait", tags=["Student Portrait"])

# SQLAlchemy Model
class Portrait(Base):
    __tablename__ = "portraits"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255))
    avatar_url = Column(Text)
    learning_style = Column(String(50))
    intro_zh = Column(Text)
    intro_en = Column(Text)
    strengths = Column(JSON)  # JSON array
    weaknesses = Column(JSON)  # JSON array
    research_directions = Column(JSON)  # JSON array
    education = Column(JSON)  # JSON array
    work_experience = Column(JSON)  # JSON array
    followers = Column(Integer, default=0)
    views = Column(Integer, default=0)
    join_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Pydantic Models
class GeneratePortraitRequest(BaseModel):
    student_id: str
    course_id: Optional[str] = None
    include_history: bool = True


class GroupPortraitRequest(BaseModel):
    student_ids: List[str]
    course_id: Optional[str] = None


class PatternRequest(BaseModel):
    student_id: str
    time_range: str = "30d"


class PortraitUpdateRequest(BaseModel):
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    intro_zh: Optional[str] = None
    intro_en: Optional[str] = None
    strengths: Optional[List[Dict]] = None
    weaknesses: Optional[List[Dict]] = None
    research_directions: Optional[List[str]] = None
    education: Optional[List[Dict]] = None
    work_experience: Optional[List[Dict]] = None


async def get_or_create_portrait(student_id: str) -> Portrait:
    """获取或创建画像记录"""
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(Portrait).where(Portrait.student_id == student_id)
        )
        portrait = result.scalar_one_or_none()
        
        if not portrait:
            portrait = Portrait(
                student_id=student_id,
                name=f"学生{student_id[-4:]}",
                strengths=[],
                weaknesses=[],
                research_directions=[],
                education=[],
                work_experience=[],
                learning_style="visual"
            )
            session.add(portrait)
            await session.commit()
            await session.refresh(portrait)
        
        return portrait


@router.post("/generate", response_model=ResponseModel)
async def generate_portrait(request: GeneratePortraitRequest):
    """Generate student portrait."""
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(Portrait).where(Portrait.student_id == request.student_id)
        )
        existing_portrait = result.scalar_one_or_none()
        
        if not existing_portrait:
            new_portrait = Portrait(
                student_id=request.student_id,
                learning_style="visual",
                strengths=["逻辑思维", "问题分析"],
                weaknesses=["粗心大意", "时间管理"],
                research_directions=[],
                education=[],
                work_experience=[],
                join_date=datetime.utcnow()
            )
            session.add(new_portrait)
            await session.commit()
            await session.refresh(new_portrait)
            
            return ResponseModel(
                code=200,
                message="success",
                data={
                    "student_id": new_portrait.student_id,
                    "learning_style": new_portrait.learning_style,
                    "strengths": new_portrait.strengths or [],
                    "weaknesses": new_portrait.weaknesses or [],
                    "learning_patterns": {
                        "preferred_time": "morning",
                        "avg_session_duration": 45,
                        "best_learning_days": ["周一", "周三", "周五"]
                    }
                }
            )
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "student_id": existing_portrait.student_id,
            "learning_style": existing_portrait.learning_style,
            "strengths": existing_portrait.strengths or [],
            "weaknesses": existing_portrait.weaknesses or [],
            "learning_patterns": {
                "preferred_time": "morning",
                "avg_session_duration": 45,
                "best_learning_days": ["周一", "周三", "周五"]
            }
        }
    )


@router.get("/{student_id}", response_model=ResponseModel)
async def get_portrait(student_id: str, course_id: str = Query(None)):
    """Get student portrait from PostgreSQL."""
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(Portrait).where(Portrait.student_id == student_id)
        )
        portrait = result.scalar_one_or_none()
        
        if not portrait:
            # Return default data
            return ResponseModel(
                code=200,
                message="success",
                data={
                    "student_id": student_id,
                    "name": f"学生{student_id[-4:]}",
                    "avatar_url": None,
                    "join_date": datetime.utcnow().strftime("%Y-%m-%d"),
                    "followers": 0,
                    "views": 0,
                    "intro": {"zh": "", "en": ""},
                    "research_directions": [],
                    "education": [],
                    "work_experience": []
                }
            )
        
        return ResponseModel(
            code=200,
            message="success",
            data={
                "student_id": portrait.student_id,
                "name": portrait.name,
                "avatar_url": portrait.avatar_url,
                "join_date": portrait.join_date.strftime("%Y-%m-%d") if portrait.join_date else None,
                "followers": portrait.followers or 0,
                "views": portrait.views or 0,
                "intro": {
                    "zh": portrait.intro_zh or "",
                    "en": portrait.intro_en or ""
                },
                "research_directions": portrait.research_directions or [],
                "education": portrait.education or [],
                "work_experience": portrait.work_experience or []
            }
        )


@router.post("/group", response_model=ResponseModel)
async def generate_group_portrait(request: GroupPortraitRequest):
    """Generate group portrait."""
    portrait = {
        "group_size": len(request.student_ids),
        "common_strengths": ["积极参与", "团队协作"],
        "common_weaknesses": ["基础知识薄弱"],
        "distribution": {
            "learning_style": {"visual": 40, "auditory": 30, "kinesthetic": 30}
        }
    }
    return ResponseModel(code=200, message="success", data=portrait)


@router.post("/pattern", response_model=ResponseModel)
async def analyze_pattern(request: PatternRequest):
    """Analyze learning patterns."""
    pattern = {
        "student_id": request.student_id,
        "active_hours": ["09:00-11:00", "14:00-16:00"],
        "preferred_days": ["周一", "周三", "周五"],
        "study_duration_avg": 45,
        "patterns": ["碎片化学习", "偏好晚间复习"]
    }
    return ResponseModel(code=200, message="success", data=pattern)


@router.get("/{student_id}/strengths", response_model=ResponseModel)
async def get_strengths(student_id: str, course_id: str = Query(None)):
    """Get student learning strengths."""
    portrait = await get_or_create_portrait(student_id)
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "strengths": portrait.strengths or [
                {"knowledge_point": "Python基础", "mastery_level": 0.85, "evidence": ["作业正确率90%", "测验满分"]},
                {"knowledge_point": "数据结构", "mastery_level": 0.78, "evidence": ["项目完成质量高"]}
            ]
        }
    )


@router.get("/{student_id}/weaknesses", response_model=ResponseModel)
async def get_weaknesses(student_id: str, course_id: str = Query(None)):
    """Get student learning weaknesses."""
    portrait = await get_or_create_portrait(student_id)
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "weaknesses": portrait.weaknesses or [
                {"knowledge_point": "算法设计", "mastery_level": 0.45, "suggestions": ["多做练习", "参考典型案例"]},
                {"knowledge_point": "代码优化", "mastery_level": 0.52, "suggestions": ["学习性能分析工具"]}
            ]
        }
    )


@router.get("/{student_id}/progress", response_model=ResponseModel)
async def get_progress(student_id: str, course_id: str = Query(None)):
    """Get student learning progress."""
    return ResponseModel(
        code=200,
        message="success",
        data={
            "total_knowledge_points": 100,
            "mastered_count": 35,
            "learning_count": 45,
            "progress_percentage": 35.0
        }
    )


@router.post("/compare", response_model=ResponseModel)
async def compare_portraits(
    student_id_1: str = Query(...),
    student_id_2: str = Query(...),
    course_id: str = Query(None)
):
    """Compare two student portraits."""
    return ResponseModel(
        code=200,
        message="success",
        data={
            "similarity_score": 0.72,
            "common_strengths": ["逻辑思维", "问题分析"],
            "common_weaknesses": ["时间管理"],
            "differences": {"learning_style": "visual vs auditory"}
        }
    )


@router.put("/{student_id}", response_model=ResponseModel)
async def update_portrait(student_id: str, data: Dict[str, Any]):
    """Update student portrait in PostgreSQL."""
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(Portrait).where(Portrait.student_id == student_id)
        )
        portrait = result.scalar_one_or_none()
        
        if not portrait:
            portrait = Portrait(student_id=student_id)
            session.add(portrait)
        
        if "name" in data:
            portrait.name = data["name"]
        if "avatar_url" in data:
            portrait.avatar_url = data["avatar_url"]
        if "intro" in data:
            if isinstance(data["intro"], dict):
                if "zh" in data["intro"]:
                    portrait.intro_zh = data["intro"]["zh"]
                if "en" in data["intro"]:
                    portrait.intro_en = data["intro"]["en"]
        if "strengths" in data:
            portrait.strengths = data["strengths"]
        if "weaknesses" in data:
            portrait.weaknesses = data["weaknesses"]
        if "research_directions" in data:
            portrait.research_directions = data["research_directions"]
        if "education" in data:
            portrait.education = data["education"]
        if "work_experience" in data:
            portrait.work_experience = data["work_experience"]
        
        portrait.updated_at = datetime.utcnow()
        await session.commit()
        await session.refresh(portrait)
        
        return ResponseModel(code=200, message="success", data={
            "student_id": portrait.student_id,
            "name": portrait.name,
            "avatar_url": portrait.avatar_url,
            "intro": {
                "zh": portrait.intro_zh or "",
                "en": portrait.intro_en or ""
            }
        })
