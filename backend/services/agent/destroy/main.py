""":param id: """
from fastapi import APIRouter
from common.models.response import ResponseModel
router = APIRouter(prefix="/agent/destroy", tags=["Agent Destroy"])

@router.delete("/{agent_id}", response_model=ResponseModel)
async def destroy_agent(agent_id: str):
    return ResponseModel(code=200, message="Agent注销成功", data={"agent_id": agent_id, "status": "destroyed"})
