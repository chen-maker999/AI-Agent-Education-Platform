"""反馈收集服务 (FEEDBACK-COLLECTOR) - PostgreSQL存储"""

import uuid
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

router = APIRouter(prefix="/feedback", tags=["Feedback Collector"])


@router.get("/", response_model=dict)
async def get_feedback_list():
    """获取反馈列表"""
    return {"code": 200, "message": "success", "data": []}


# SQLAlchemy
from sqlalchemy import Column, String, Integer, DateTime, Text, Float, JSON
from sqlalchemy.dialects.postgresql import UUID
from common.database.postgresql import Base, AsyncSessionLocal


class Feedback(Base):
    __tablename__ = "feedbacks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    feedback_id = Column(String(100), unique=True, index=True)
    answer_id = Column(String(100), index=True)
    rating = Column(Integer)
    feedback_type = Column(String(50))
    comment = Column(Text)
    correction = Column(Text)
    student_id = Column(String(100), index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class FeedbackRequest(BaseModel):
    answer_id: Optional[str] = None
    rating: Optional[int] = None
    feedback_type: str = "general"
    comment: Optional[str] = None
    correction: Optional[str] = None
    student_id: str


class FeedbackRequestSimple(BaseModel):
    """简化版反馈请求"""
    student_id: str
    content: str = "good"
    rating: Optional[int] = 5
    feedback_type: Optional[str] = "general"


@router.post("/submit")
async def submit_feedback(request: FeedbackRequest):
    """提交反馈"""
    feedback_id = f"fb_{datetime.utcnow().timestamp()}"
    
    async with AsyncSessionLocal() as session:
        feedback = Feedback(
            feedback_id=feedback_id,
            answer_id=request.answer_id or f"ans_{datetime.now().timestamp()}",
            rating=request.rating,
            feedback_type=request.feedback_type,
            comment=request.comment,
            correction=request.correction,
            student_id=request.student_id
        )
        session.add(feedback)
        await session.commit()
    
    return {"code": 200, "message": "反馈已提交", "data": {"feedback_id": feedback_id}}


@router.post("/submit/simple")
async def submit_feedback_simple(request: FeedbackRequestSimple):
    """简化版反馈提交"""
    feedback_id = f"fb_{datetime.utcnow().timestamp()}"
    
    async with AsyncSessionLocal() as session:
        feedback = Feedback(
            feedback_id=feedback_id,
            answer_id=f"ans_{datetime.now().timestamp()}",
            rating=request.rating,
            feedback_type=request.feedback_type or "general",
            comment=request.content,
            student_id=request.student_id
        )
        session.add(feedback)
        await session.commit()
    
    return {"code": 200, "message": "反馈已提交", "data": {"feedback_id": feedback_id}}


@router.get("/answer/{answer_id}")
async def get_answer_feedback(answer_id: str):
    """获取答案的所有反馈"""
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(Feedback).where(Feedback.answer_id == answer_id)
        )
        feedbacks = result.scalars().all()
        
        items = [{
            "feedback_id": f.feedback_id,
            "answer_id": f.answer_id,
            "rating": f.rating,
            "feedback_type": f.feedback_type,
            "comment": f.comment,
            "correction": f.correction,
            "student_id": f.student_id,
            "created_at": f.created_at.isoformat() if f.created_at else None
        } for f in feedbacks]
        
        return {"code": 200, "data": {"feedbacks": items, "count": len(items)}}


@router.get("/student/{student_id}")
async def get_student_feedback(student_id: str):
    """获取学生的所有反馈"""
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(Feedback).where(Feedback.student_id == student_id).order_by(Feedback.created_at.desc())
        )
        feedbacks = result.scalars().all()
        
        items = [{
            "feedback_id": f.feedback_id,
            "answer_id": f.answer_id,
            "rating": f.rating,
            "feedback_type": f.feedback_type,
            "comment": f.comment,
            "created_at": f.created_at.isoformat() if f.created_at else None
        } for f in feedbacks]
        
        return {"code": 200, "data": {"feedbacks": items, "count": len(items)}}


@router.get("/stats")
async def get_feedback_stats():
    """获取反馈统计"""
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select, func, avg
        
        total_result = await session.execute(select(func.count(Feedback.id)))
        total = total_result.scalar() or 0
        
        avg_result = await session.execute(select(avg(Feedback.rating)).where(Feedback.rating != None))
        avg_rating = avg_result.scalar() or 0
        
        return {"code": 200, "data": {"total": total, "avg_rating": round(float(avg_rating), 2)}}
