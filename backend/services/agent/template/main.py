"""AGENT - Template management service."""
from uuid import uuid4
from datetime import datetime
from typing import List, Dict, Any
from fastapi import APIRouter, Query
from pydantic import BaseModel
from common.models.response import ResponseModel
router = APIRouter(prefix="/agent/template", tags=["Agent Template"])

agent_templates = [
    {"id": "1", "name": "答疑Agent", "type": "chat", "config": {"llm": "kimi", "rag_enabled": True}},
    {"id": "2", "name": "批改Agent", "type": "grading", "config": {"auto_grade": True}},
]

@router.get("", response_model=ResponseModel)
async def list_templates():
    return ResponseModel(code=200, message="success", data={"templates": agent_templates})

@router.get("/{template_id}", response_model=ResponseModel)
async def get_template(template_id: str):
    for t in agent_templates:
        if t["id"] == template_id:
            return ResponseModel(code=200, message="success", data=t)
    return ResponseModel(code=404, message="Template not found")

@router.post("", response_model=ResponseModel)
async def create_template(data: Dict[str, Any]):
    template = {"id": str(uuid4()), **data, "created_at": datetime.utcnow().isoformat()}
    agent_templates.append(template)
    return ResponseModel(code=201, message="success", data=template)
