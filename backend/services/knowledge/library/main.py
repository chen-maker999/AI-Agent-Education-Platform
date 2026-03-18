"""Knowledge base (KB) management service - PostgreSQL storage.

This is the "container" entity for documents. We map kb_id -> course_id in existing RAG APIs.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, JSON, String, Text, select, func
from sqlalchemy.dialects.postgresql import UUID

from common.database.postgresql import Base, AsyncSessionLocal, async_engine

router = APIRouter(prefix="/knowledge/library", tags=["Knowledge Library"])


class KnowledgeBaseDB(Base):
    __tablename__ = "knowledge_bases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kb_id = Column(String(100), unique=True, index=True)
    owner_id = Column(String(100), index=True)  # user id
    name = Column(String(255), nullable=False)
    description = Column(Text)
    settings = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


_kb_db_inited = False


async def _ensure_tables():
    global _kb_db_inited
    if _kb_db_inited:
        return
    from sqlalchemy import text

    async with async_engine.begin() as conn:
        await conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS knowledge_bases (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    kb_id VARCHAR(100) UNIQUE,
                    owner_id VARCHAR(100),
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    settings JSONB DEFAULT '{}'::jsonb,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        await conn.commit()
    _kb_db_inited = True


class KnowledgeBaseCreate(BaseModel):
    owner_id: str
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = ""
    settings: Dict[str, Any] = Field(default_factory=dict)


class KnowledgeBaseUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


def _to_item(kb: KnowledgeBaseDB) -> Dict[str, Any]:
    return {
        "kb_id": kb.kb_id,
        "owner_id": kb.owner_id,
        "name": kb.name,
        "description": kb.description or "",
        "settings": kb.settings or {},
        "created_at": kb.created_at.isoformat() if kb.created_at else None,
        "updated_at": kb.updated_at.isoformat() if kb.updated_at else None,
    }


@router.post("", summary="Create a knowledge base")
async def create_kb(payload: KnowledgeBaseCreate):
    await _ensure_tables()
    kb_id = f"kb_{uuid.uuid4().hex[:12]}"
    async with AsyncSessionLocal() as session:
        kb = KnowledgeBaseDB(
            kb_id=kb_id,
            owner_id=payload.owner_id,
            name=payload.name,
            description=payload.description or "",
            settings=payload.settings or {},
        )
        session.add(kb)
        await session.commit()
        await session.refresh(kb)
        return {"code": 200, "message": "success", "data": _to_item(kb)}


@router.get("/my", summary="List my knowledge bases")
async def list_my_kbs(
    owner_id: str = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    await _ensure_tables()
    async with AsyncSessionLocal() as session:
        count_result = await session.execute(
            select(func.count(KnowledgeBaseDB.id)).where(KnowledgeBaseDB.owner_id == owner_id)
        )
        total = count_result.scalar() or 0

        result = await session.execute(
            select(KnowledgeBaseDB)
            .where(KnowledgeBaseDB.owner_id == owner_id)
            .order_by(KnowledgeBaseDB.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = [_to_item(x) for x in result.scalars().all()]
        return {"code": 200, "message": "success", "data": {"items": items, "total": total}}


@router.get("/{kb_id}", summary="Get knowledge base")
async def get_kb(kb_id: str):
    await _ensure_tables()
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(KnowledgeBaseDB).where(KnowledgeBaseDB.kb_id == kb_id))
        kb = result.scalar_one_or_none()
        if not kb:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        return {"code": 200, "message": "success", "data": _to_item(kb)}


@router.put("/{kb_id}", summary="Update knowledge base")
async def update_kb(kb_id: str, payload: KnowledgeBaseUpdate):
    await _ensure_tables()
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(KnowledgeBaseDB).where(KnowledgeBaseDB.kb_id == kb_id))
        kb = result.scalar_one_or_none()
        if not kb:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        if payload.name is not None:
            kb.name = payload.name
        if payload.description is not None:
            kb.description = payload.description
        if payload.settings is not None:
            kb.settings = payload.settings
        await session.commit()
        await session.refresh(kb)
        return {"code": 200, "message": "success", "data": _to_item(kb)}


@router.delete("/{kb_id}", summary="Delete knowledge base")
async def delete_kb(kb_id: str):
    await _ensure_tables()
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(KnowledgeBaseDB).where(KnowledgeBaseDB.kb_id == kb_id))
        kb = result.scalar_one_or_none()
        if not kb:
            return {"code": 200, "message": "success", "data": {"deleted": False}}
        await session.delete(kb)
        await session.commit()
        return {"code": 200, "message": "success", "data": {"deleted": True}}

