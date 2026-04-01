"""Response models for API."""

from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel, Field


class ResponseModel(BaseModel):
    """Base response model."""

    code: int = Field(default=200, description="Response code")
    message: str = Field(default="success", description="Response message")
    data: Optional[Any] = Field(default=None, description="Response data")


class PageResult(BaseModel):
    """Paginated result."""

    items: list[Any] = Field(default_factory=list, description="Data items")
    total: int = Field(default=0, description="Total count")
    page: int = Field(default=1, description="Current page")
    page_size: int = Field(default=10, description="Page size")
    total_pages: int = Field(default=0, description="Total pages")


class TokenResponse(BaseModel):
    """Token response."""

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600


class UserResponse(BaseModel):
    """User response."""

    id: str
    username: str
    email: str
    phone: Optional[str] = None
    role: str
    status: str = "active"
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response."""

    code: int = Field(default=400, description="Error code")
    message: str = Field(default="Error", description="Error message")
    error: Optional[str] = Field(default=None, description="Detailed error")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


from datetime import datetime
