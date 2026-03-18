"""Data collection service - Learning behavior and homework data collection."""

from uuid import uuid4
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from common.models.response import ResponseModel
from common.core.config import settings
from kafka import KafkaProducer
import json

router = APIRouter(prefix="/collect", tags=["Data Collection"])

# Kafka producer
kafka_producer = None

def get_kafka_producer():
    global kafka_producer
    if kafka_producer is None:
        try:
            kafka_producer = KafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
        except Exception:
            pass
    return kafka_producer


# Request/Response models
class BehaviorData(BaseModel):
    student_id: str
    course_id: str = "default"
    session_id: str = "default"
    device_type: str = "web"
    platform: str = "self"
    watch_duration: int = 0
    attention_score: float = 0
    interaction_count: int = 0
    scroll_depth: float = 0
    event_time: Optional[str] = None
    extra_data: Dict[str, Any] = {}


class BehaviorDataSimple(BaseModel):
    """简化版行为数据，用于简单采集"""
    student_id: str
    event: str = "login"
    timestamp: Optional[str] = None
    event_type: Optional[str] = "behavior"
    duration: Optional[int] = 0
    metadata: Optional[Dict[str, Any]] = {}


class HomeworkData(BaseModel):
    homework_id: str
    student_id: str
    course_id: str
    platform: str = "self"
    submit_time: Optional[str] = None
    content_type: str = "text"
    content: str = ""
    file_url: Optional[str] = None
    file_hash: Optional[str] = None
    version: int = 1
    extra_data: Dict[str, Any] = {}


class BatchCollectRequest(BaseModel):
    behavior_data: List[Dict[str, Any]] = []
    homework_data: List[Dict[str, Any]] = []


# In-memory storage for demo
collected_behaviors = []
collected_homeworks = []


@router.post("/behavior", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
async def collect_behavior(data: BehaviorData):
    """Collect learning behavior data."""
    record = {
        "id": str(uuid4()),
        **data.model_dump(),
        "collected_at": datetime.utcnow().isoformat()
    }
    collected_behaviors.append(record)
    
    # Send to Kafka
    producer = get_kafka_producer()
    if producer:
        try:
            producer.send("learning-behavior", value=record)
        except Exception:
            pass
    
    return ResponseModel(
        code=201,
        message="学习行为数据采集完成",
        data={
            "id": record["id"],
            "status": "success",
            "collected_at": record["collected_at"]
        }
    )


@router.post("/behavior/simple", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
async def collect_behavior_simple(data: BehaviorDataSimple):
    """简化版行为数据采集"""
    record = {
        "id": str(uuid4()),
        "student_id": data.student_id,
        "event": data.event,
        "course_id": "default",
        "session_id": data.timestamp or str(uuid4()),
        "event_time": data.timestamp or datetime.utcnow().isoformat(),
        "watch_duration": data.duration or 0,
        "extra_data": data.metadata or {},
        "collected_at": datetime.utcnow().isoformat()
    }
    collected_behaviors.append(record)
    
    return ResponseModel(
        code=201,
        message="学习行为数据采集完成",
        data={
            "id": record["id"],
            "status": "success",
            "collected_at": record["collected_at"]
        }
    )


@router.post("/homework", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
async def collect_homework(data: HomeworkData):
    """Collect homework submission data."""
    record = {
        "id": str(uuid4()),
        **data.model_dump(),
        "collected_at": datetime.utcnow().isoformat()
    }
    collected_homeworks.append(record)
    
    # Send to Kafka
    producer = get_kafka_producer()
    if producer:
        try:
            producer.send("homework-submission", value=record)
        except Exception:
            pass
    
    return ResponseModel(
        code=201,
        message="作业数据采集完成",
        data={
            "id": record["id"],
            "status": "success",
            "collected_at": record["collected_at"]
        }
    )


@router.post("/batch", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
async def batch_collect(data: BatchCollectRequest):
    """Batch collect data."""
    behavior_count = 0
    homework_count = 0
    
    for item in data.behavior_data:
        record = {
            "id": str(uuid4()),
            **item,
            "collected_at": datetime.utcnow().isoformat()
        }
        collected_behaviors.append(record)
        behavior_count += 1
    
    for item in data.homework_data:
        record = {
            "id": str(uuid4()),
            **item,
            "collected_at": datetime.utcnow().isoformat()
        }
        collected_homeworks.append(record)
        homework_count += 1
    
    return ResponseModel(
        code=201,
        message="批量数据采集完成",
        data={
            "behavior_count": behavior_count,
            "homework_count": homework_count,
            "status": "success"
        }
    )


@router.get("/status", response_model=ResponseModel)
async def get_status():
    """Get collection service status."""
    return ResponseModel(
        code=200,
        message="获取采集状态成功",
        data={
            "service_status": "running",
            "kafka_connected": kafka_producer is not None,
            "total_collected": len(collected_behaviors) + len(collected_homeworks),
            "today_collected": len(collected_behaviors) + len(collected_homeworks),
            "last_collect_time": datetime.utcnow().isoformat()
        }
    )


@router.post("/adapt/{platform}", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
async def adapt_platform_data(platform: str, data: Dict[str, Any]):
    """Adapt third-party platform data to standard format."""
    adapted_count = 0
    
    # Platform-specific adaptation logic would go here
    # For demo, just count items
    if isinstance(data, list):
        adapted_count = len(data)
    else:
        adapted_count = 1
    
    return ResponseModel(
        code=201,
        message="平台数据适配完成",
        data={
            "adapted_count": adapted_count,
            "status": "success"
        }
    )
