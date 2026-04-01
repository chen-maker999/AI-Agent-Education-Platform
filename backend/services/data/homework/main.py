"""Homework storage service - Real MinIO + PostgreSQL storage."""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from common.models.response import ResponseModel
from common.core.config import settings
from common.database.postgresql import Base, AsyncSessionLocal, get_db
from minio import Minio
from minio.error import S3Error
import hashlib
import io

router = APIRouter(prefix="/homework", tags=["Homework Storage"])

# MinIO 不可用时写入 backend/local_storage/homework/<object_name>
LOCAL_HOMEWORK_URL_PREFIX = "local://"


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[3]


def local_homework_root() -> Path:
    p = _backend_root() / "local_storage" / "homework"
    p.mkdir(parents=True, exist_ok=True)
    return p


def save_homework_local(object_name: str, content: bytes) -> str:
    safe = object_name.replace("\\", "/").strip("/")
    path = local_homework_root() / safe
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return f"{LOCAL_HOMEWORK_URL_PREFIX}{safe}"


def read_homework_local(file_url: str) -> Optional[bytes]:
    if not file_url.startswith(LOCAL_HOMEWORK_URL_PREFIX):
        return None
    rel = file_url[len(LOCAL_HOMEWORK_URL_PREFIX) :].lstrip("/")
    path = local_homework_root() / rel
    if not path.is_file():
        return None
    return path.read_bytes()


def delete_homework_local_file(file_url: str) -> None:
    if not file_url.startswith(LOCAL_HOMEWORK_URL_PREFIX):
        return
    rel = file_url[len(LOCAL_HOMEWORK_URL_PREFIX) :].lstrip("/")
    path = local_homework_root() / rel
    if path.is_file():
        try:
            path.unlink()
        except OSError:
            pass


# SQLAlchemy Model
class Homework(Base):
    __tablename__ = "homework"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    homework_id = Column(String(255), unique=True, index=True, nullable=False)
    student_id = Column(String(255), index=True, nullable=False)
    filename = Column(String(500), nullable=False)
    file_url = Column(Text, nullable=False)
    file_hash = Column(String(64), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    status = Column(String(50), default="pending")
    course = Column(String(100))
    note = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# MinIO Client
def get_minio_client() -> Minio:
    """Get MinIO client."""
    return Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE
    )


async def init_minio_bucket():
    """Initialize MinIO bucket if not exists."""
    try:
        client = get_minio_client()
        if not client.bucket_exists(settings.MINIO_BUCKET_HOMEWORK):
            client.make_bucket(settings.MINIO_BUCKET_HOMEWORK)
    except Exception as e:
        print(f"MinIO bucket init warning: {e}")
        # MinIO不可用时继续运行，不阻止应用启动


# Pydantic Models
class HomeworkCreate(BaseModel):
    homework_id: str
    student_id: str
    filename: str
    file_url: str
    file_hash: str
    file_size: int
    mime_type: str
    status: str = "pending"
    course: Optional[str] = None
    note: Optional[str] = None


class HomeworkResponse(BaseModel):
    homework_id: str
    student_id: str
    filename: str
    file_url: str
    file_size: int
    mime_type: str
    status: str
    course: Optional[str]
    note: Optional[str]
    created_at: datetime
    updated_at: datetime


# Initialize MinIO on startup (disabled - lazy init)
# @router.on_event("startup")
# async def startup_event():
#     await init_minio_bucket()


@router.post("/upload", response_model=ResponseModel)
async def upload_homework(
    homework_id: str = Form(...),
    student_id: str = Form(...),
    course: str = Form(None),
    note: str = Form(None),
    file: UploadFile = File(...)
):
    """Upload homework file to MinIO storage."""
    try:
        # Read file content
        content = await file.read()
        file_size = len(content)
        file_hash = hashlib.sha256(content).hexdigest()
        mime_type = file.content_type or "application/octet-stream"
        
        # Generate unique object name
        object_name = f"{student_id}/{homework_id}/{file.filename}"
        
        file_url: str
        client = get_minio_client()
        try:
            if not client.bucket_exists(settings.MINIO_BUCKET_HOMEWORK):
                client.make_bucket(settings.MINIO_BUCKET_HOMEWORK)
            client.put_object(
                settings.MINIO_BUCKET_HOMEWORK,
                object_name,
                io.BytesIO(content),
                length=file_size,
                content_type=mime_type,
            )
            file_url = f"http://{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET_HOMEWORK}/{object_name}"
        except Exception as e:
            # MinIO 未启动或网络不可达时落盘，避免上传接口 500
            file_url = save_homework_local(object_name, content)
            print(f"MinIO upload skipped, using local storage: {e}")
        
        # Save metadata to PostgreSQL
        async with AsyncSessionLocal() as session:
            homework = Homework(
                homework_id=homework_id,
                student_id=student_id,
                filename=file.filename,
                file_url=file_url,
                file_hash=file_hash,
                file_size=file_size,
                mime_type=mime_type,
                status="uploaded",
                course=course,
                note=note
            )
            session.add(homework)
            await session.commit()
            await session.refresh(homework)
        
        return ResponseModel(
            code=200,
            message="作业文件上传成功",
            data={
                "homework_id": homework_id,
                "file_url": file_url,
                "file_hash": file_hash,
                "file_size": file_size,
                "mime_type": mime_type,
                "uploaded_at": datetime.utcnow().isoformat()
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/{homework_id}/raw")
async def download_homework_raw(homework_id: str):
    """直接下载作业文件（本地存储时经后端读出；MinIO 时 302 到预签名 URL）。"""
    from sqlalchemy import select
    from datetime import timedelta

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Homework).where(Homework.homework_id == homework_id))
        homework = result.scalar_one_or_none()

    if not homework:
        raise HTTPException(status_code=404, detail="Homework not found")

    if homework.file_url.startswith(LOCAL_HOMEWORK_URL_PREFIX):
        rel = homework.file_url[len(LOCAL_HOMEWORK_URL_PREFIX) :].lstrip("/")
        path = local_homework_root() / rel
        if not path.is_file():
            raise HTTPException(status_code=404, detail="本地文件不存在")
        return FileResponse(
            path,
            filename=homework.filename,
            media_type=homework.mime_type or "application/octet-stream",
        )

    client = get_minio_client()
    object_name = f"{homework.student_id}/{homework_id}/{homework.filename}"
    try:
        presigned_url = client.presigned_get_object(
            settings.MINIO_BUCKET_HOMEWORK,
            object_name,
            expires=timedelta(seconds=3600),
        )
        return RedirectResponse(url=presigned_url)
    except S3Error:
        raise HTTPException(status_code=404, detail="无法从 MinIO 获取文件")


@router.get("/{homework_id}/download", response_model=ResponseModel)
async def get_download_url(
    homework_id: str,
    expires: int = Query(3600, ge=1, le=86400)
):
    """Get homework file download URL from MinIO."""
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(Homework).where(Homework.homework_id == homework_id)
        )
        homework = result.scalar_one_or_none()
        
        if not homework:
            raise HTTPException(status_code=404, detail="Homework not found")

        if homework.file_url.startswith(LOCAL_HOMEWORK_URL_PREFIX):
            return ResponseModel(
                code=200,
                message="获取下载链接成功",
                data={
                    "download_url": f"/api/v1/homework/{homework_id}/raw",
                    "expires_at": datetime.utcnow().isoformat(),
                },
            )
        
        # Generate presigned URL from MinIO
        client = get_minio_client()
        object_name = f"{homework.student_id}/{homework_id}/{homework.filename}"
        
        try:
            from datetime import timedelta
            presigned_url = client.presigned_get_object(
                settings.MINIO_BUCKET_HOMEWORK,
                object_name,
                expires=timedelta(seconds=expires)
            )
        except S3Error:
            # Fallback to direct URL if presigned fails
            presigned_url = homework.file_url
        
        return ResponseModel(
            code=200,
            message="获取下载链接成功",
            data={
                "download_url": presigned_url,
                "expires_at": datetime.utcnow().isoformat()
            }
        )


@router.get("/{homework_id}", response_model=ResponseModel)
async def get_homework(homework_id: str):
    """Get homework file info from PostgreSQL."""
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(Homework).where(Homework.homework_id == homework_id)
        )
        homework = result.scalar_one_or_none()
        
        if not homework:
            raise HTTPException(status_code=404, detail="Homework not found")
        
        return ResponseModel(
            code=200,
            message="查询成功",
            data={
                "homework_id": homework.homework_id,
                "student_id": homework.student_id,
                "filename": homework.filename,
                "file_url": homework.file_url,
                "file_size": homework.file_size,
                "mime_type": homework.mime_type,
                "status": homework.status,
                "course": homework.course,
                "note": homework.note,
                "created_at": homework.created_at.isoformat() if homework.created_at else None,
                "updated_at": homework.updated_at.isoformat() if homework.updated_at else None
            }
        )


@router.delete("/{homework_id}", response_model=ResponseModel)
async def delete_homework(homework_id: str):
    """Delete homework file from MinIO and PostgreSQL."""
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select, delete
        result = await session.execute(
            select(Homework).where(Homework.homework_id == homework_id)
        )
        homework = result.scalar_one_or_none()
        
        if not homework:
            raise HTTPException(status_code=404, detail="Homework not found")
        
        # Delete from MinIO or local
        if homework.file_url.startswith(LOCAL_HOMEWORK_URL_PREFIX):
            delete_homework_local_file(homework.file_url)
        else:
            client = get_minio_client()
            object_name = f"{homework.student_id}/{homework_id}/{homework.filename}"
            try:
                client.remove_object(settings.MINIO_BUCKET_HOMEWORK, object_name)
            except S3Error:
                pass
        
        # Delete from PostgreSQL
        await session.execute(
            delete(Homework).where(Homework.homework_id == homework_id)
        )
        await session.commit()
        
        return ResponseModel(code=200, message="删除成功")


@router.get("", response_model=ResponseModel)
async def list_homework(
    student_id: str = Query(None),
    homework_id: str = Query(None),
    status: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    """List homework files from PostgreSQL."""
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select, func, or_
        
        # Build query
        query = select(Homework)
        count_query = select(func.count(Homework.id))
        
        conditions = []
        if student_id:
            conditions.append(Homework.student_id == student_id)
        if homework_id:
            conditions.append(Homework.homework_id == homework_id)
        if status:
            conditions.append(Homework.status == status)
        
        if conditions:
            query = query.where(*conditions)
            count_query = count_query.where(*conditions)
        
        # Get total count
        total_result = await session.execute(count_query)
        total = total_result.scalar() or 0
        
        # Get paginated results
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await session.execute(query)
        homeworks = result.scalars().all()
        
        items = [{
            "homework_id": h.homework_id,
            "student_id": h.student_id,
            "filename": h.filename,
            "file_url": h.file_url,
            "file_size": h.file_size,
            "mime_type": h.mime_type,
            "status": h.status,
            "course": h.course,
            "note": h.note,
            "created_at": h.created_at.isoformat() if h.created_at else None,
            "updated_at": h.updated_at.isoformat() if h.updated_at else None
        } for h in homeworks]
        
        return ResponseModel(
            code=200,
            message="查询成功",
            data={
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size
            }
        )


@router.get("/{homework_id}/presigned", response_model=ResponseModel)
async def get_presigned_url(
    homework_id: str,
    method: str = Query("GET"),
    expires: int = Query(3600)
):
    """Get presigned URL for homework file from MinIO."""
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(Homework).where(Homework.homework_id == homework_id)
        )
        homework = result.scalar_one_or_none()
        
        if not homework:
            raise HTTPException(status_code=404, detail="Homework not found")
        
        client = get_minio_client()
        object_name = f"{homework.student_id}/{homework_id}/{homework.filename}"
        
        try:
            from datetime import timedelta
            if method == "GET":
                presigned_url = client.presigned_get_object(
                    settings.MINIO_BUCKET_HOMEWORK,
                    object_name,
                    expires=timedelta(seconds=expires)
                )
            else:
                presigned_url = client.presigned_put_object(
                    settings.MINIO_BUCKET_HOMEWORK,
                    object_name,
                    expires=timedelta(seconds=expires)
                )
        except S3Error:
            presigned_url = homework.file_url
        
        return ResponseModel(
            code=200,
            message="获取预签名URL成功",
            data={
                "url": presigned_url,
                "method": method,
                "expires_at": datetime.utcnow().isoformat()
            }
        )


@router.get("/statistics/summary", response_model=ResponseModel)
async def get_statistics(student_id: str = Query(None)):
    """Get homework statistics from PostgreSQL."""
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select, func
        
        # Base query
        base_query = select(Homework)
        if student_id:
            base_query = base_query.where(Homework.student_id == student_id)
        
        # Get all matching records
        result = await session.execute(base_query)
        homeworks = result.scalars().all()
        
        total_files = len(homeworks)
        total_size = sum(h.file_size for h in homeworks)
        
        by_status = {}
        by_type = {}
        for h in homeworks:
            by_status[h.status] = by_status.get(h.status, 0) + 1
            by_type[h.mime_type] = by_type.get(h.mime_type, 0) + 1
        
        return ResponseModel(
            code=200,
            message="获取统计信息成功",
            data={
                "total_files": total_files,
                "total_size": total_size,
                "by_status": by_status,
                "by_type": by_type
            }
        )


@router.patch("/{homework_id}/status", response_model=ResponseModel)
async def update_status(homework_id: str, status: str = Query(...)):
    """Update homework file status in PostgreSQL."""
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select, update
        result = await session.execute(
            select(Homework).where(Homework.homework_id == homework_id)
        )
        homework = result.scalar_one_or_none()
        
        if not homework:
            raise HTTPException(status_code=404, detail="Homework not found")
        
        homework.status = status
        homework.updated_at = datetime.utcnow()
        await session.commit()
        
        return ResponseModel(code=200, message="状态更新成功")
