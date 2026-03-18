""":param id: """
from uuid import uuid4
from fastapi import APIRouter
from common.models.response import ResponseModel
router = APIRouter(prefix="/agent/deploy", tags=["Agent Deploy"])

@router.post("", response_model=ResponseModel)
async def deploy_agent(agent_id: str, config: dict):
    return ResponseModel(code=200, message="部署成功", data={"agent_id": agent_id, "status": "running", "pod": "agent-pod-1"})

@router.get("/{agent_id}/status", response_model=ResponseModel)
async def get_deploy_status(agent_id: str):
    return ResponseModel(code=200, message="success", data={"agent_id": agent_id, "status": "running", "replicas": 1})
