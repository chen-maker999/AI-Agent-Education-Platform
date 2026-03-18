"""ADAPT - Sync service for cross-platform data sync."""
from fastapi import APIRouter, Query
from common.models.response import ResponseModel
router = APIRouter(prefix="/adapt/sync", tags=["Platform Sync"])

@router.get("/status", response_model=ResponseModel)
async def get_sync_status():
    return ResponseModel(code=200, message="success", data={"pending": 0, "running": 0, "completed": 10})

@router.get("/jobs", response_model=ResponseModel)
async def list_sync_jobs():
    """获取同步任务列表"""
    return ResponseModel(
        code=200,
        message="success",
        data={"items": [], "total": 0}
    )

@router.post("/trigger", response_model=ResponseModel)
async def trigger_sync(platform: str = Query(...)):
    return ResponseModel(code=200, message="同步已触发", data={"task_id": "1", "platform": platform})
