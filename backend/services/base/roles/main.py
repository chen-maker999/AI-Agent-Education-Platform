"""Role management service."""

from uuid import uuid4
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from common.models.response import ResponseModel, PageResult
from common.security import decode_token
from common.core.config import settings

router = APIRouter(prefix="/roles", tags=["Roles"])


# In-memory role storage for demo
roles_db = {
    "admin": {
        "id": "1",
        "name": "Administrator",
        "code": "admin",
        "permissions": ["*"],
        "created_at": "2024-01-01T00:00:00Z"
    },
    "teacher": {
        "id": "2",
        "name": "Teacher",
        "code": "teacher",
        "permissions": ["course:read", "course:create", "student:read", "homework:grade"],
        "created_at": "2024-01-01T00:00:00Z"
    },
    "student": {
        "id": "3",
        "name": "Student",
        "code": "student",
        "permissions": ["course:read", "homework:submit", "chat:ask"],
        "created_at": "2024-01-01T00:00:00Z"
    },
}


class RoleCreate(BaseModel):
    name: str
    code: str
    permissions: List[str] = []


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    permissions: Optional[List[str]] = None


class Permission(BaseModel):
    id: str
    name: str
    code: str
    resource: str
    action: str


@router.get("", response_model=ResponseModel)
async def get_roles(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    """Get role list with pagination."""
    roles = list(roles_db.values())
    total = len(roles)
    start = (page - 1) * page_size
    end = start + page_size
    items = roles[start:end]
    
    return ResponseModel(
        code=200,
        message="查询成功",
        data={
            "items": items,
            "total": total,
            "page_num": page,
            "size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    )


@router.get("/{role_id}", response_model=ResponseModel)
async def get_role(role_id: str):
    """Get role details by ID."""
    for role in roles_db.values():
        if role["id"] == role_id:
            return ResponseModel(code=200, message="查询成功", data=role)
    raise HTTPException(status_code=404, detail="Role not found")


@router.post("", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
async def create_role(role_data: RoleCreate):
    """Create new role."""
    if role_data.code in roles_db:
        raise HTTPException(status_code=409, detail="Role code already exists")
    
    role = {
        "id": str(uuid4()),
        "name": role_data.name,
        "code": role_data.code,
        "permissions": role_data.permissions,
        "created_at": "2024-01-01T00:00:00Z"
    }
    roles_db[role_data.code] = role
    
    return ResponseModel(
        code=201,
        message="角色创建成功",
        data=role
    )


@router.put("/{role_id}", response_model=ResponseModel)
async def update_role(role_id: str, role_data: RoleUpdate):
    """Update role."""
    for key, role in roles_db.items():
        if role["id"] == role_id:
            if role_data.name:
                role["name"] = role_data.name
            if role_data.permissions:
                role["permissions"] = role_data.permissions
            return ResponseModel(code=200, message="角色更新成功", data=role)
    raise HTTPException(status_code=404, detail="Role not found")


@router.delete("/{role_id}", response_model=ResponseModel)
async def delete_role(role_id: str):
    """Delete role."""
    for key, role in roles_db.items():
        if role["id"] == role_id:
            del roles_db[key]
            return ResponseModel(code=200, message="角色删除成功")
    raise HTTPException(status_code=404, detail="Role not found")


@router.get("/{role_id}/permissions", response_model=ResponseModel)
async def get_role_permissions(role_id: str):
    """Get role permissions."""
    for role in roles_db.values():
        if role["id"] == role_id:
            permissions = []
            for i, perm in enumerate(role["permissions"]):
                permissions.append({
                    "id": str(i),
                    "name": perm.replace(":", " "),
                    "code": perm,
                    "resource": perm.split(":")[0] if ":" in perm else perm,
                    "action": perm.split(":")[1] if ":" in perm else "all"
                })
            return ResponseModel(code=200, message="查询成功", data=permissions)
    raise HTTPException(status_code=404, detail="Role not found")
