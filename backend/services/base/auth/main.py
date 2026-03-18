"""Base authentication service - JWT based auth with PostgreSQL."""

import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import Column, String, DateTime, select
from sqlalchemy.dialects.postgresql import UUID
from common.models.response import ResponseModel
from common.models.response import UserResponse
from common.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from common.core.config import settings
from common.database.postgresql import Base, AsyncSessionLocal, async_engine

router = APIRouter(prefix="/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/login")


# SQLAlchemy User Model
class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="student")
    status = Column(String(20), default="active")
    roles = Column(String(500), default="[]")
    permissions = Column(String(1000), default="[]")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Pydantic schemas
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: str = Field(default="student")


class UserLogin(BaseModel):
    username: str
    password: str


class TokenRefresh(BaseModel):
    refresh_token: str


# Initialize database tables
async def init_auth_db():
    """Initialize auth database tables."""
    from sqlalchemy import text
    async with async_engine.begin() as conn:
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                hashed_password VARCHAR(255) NOT NULL,
                role VARCHAR(20) DEFAULT 'student',
                status VARCHAR(20) DEFAULT 'active',
                roles VARCHAR(500) DEFAULT '[]',
                permissions VARCHAR(1000) DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        await conn.commit()


# Seed demo user
async def seed_demo_user():
    """Seed demo user if not exists."""
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.username == "demo"))
        demo_user = result.scalar_one_or_none()
        
        if not demo_user:
            demo_user = User(
                username="demo",
                email="demo@example.com",
                hashed_password=get_password_hash("demo123"),
                role="student",
                status="active",
                roles='["student"]',
                permissions="[]"
            )
            session.add(demo_user)
            await session.commit()


# Call initialization
import asyncio
try:
    asyncio.create_task(init_auth_db())
    asyncio.create_task(seed_demo_user())
except:
    pass


async def get_user_from_db(username: str) -> Optional[User]:
    """Get user from database."""
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()


async def create_user_db(user_data: UserCreate) -> User:
    """Create new user in database."""
    async with AsyncSessionLocal() as session:
        user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=get_password_hash(user_data.password),
            role=user_data.role,
            status="active",
            roles=f'["{user_data.role}"]',
            permissions="[]"
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
) -> UserResponse:
    """Get current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    user = await get_user_from_db(username)
    if user is None:
        raise credentials_exception
    
    return UserResponse(
        id=str(user.id),
        username=user.username,
        email=user.email,
        role=user.role,
        status=user.status,
        roles=user.roles.split(',') if user.roles else [user.role],
        permissions=user.permissions.split(',') if user.permissions else [],
        created_at=user.created_at.isoformat() if user.created_at else None,
        updated_at=user.updated_at.isoformat() if user.updated_at else None
    )


@router.post("/register", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """Register a new user."""
    existing_user = await get_user_from_db(user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already registered"
        )
    
    user = await create_user_db(user_data)
    
    return ResponseModel(
        code=201,
        message="注册成功",
        data={
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "status": user.status,
            "roles": [user.role],
            "permissions": [],
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        }
    )


@router.post("/login", response_model=ResponseModel)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """User login endpoint."""
    user = await get_user_from_db(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(data={"sub": user.username})
    
    return ResponseModel(
        code=200,
        message="登录成功",
        data={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }
    )


@router.post("/refresh", response_model=ResponseModel)
async def refresh_token(token_data: TokenRefresh):
    """Refresh access token."""
    payload = decode_token(token_data.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    
    username = payload.get("sub")
    user = await get_user_from_db(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    access_token = create_access_token(data={"sub": username})
    new_refresh_token = create_refresh_token(data={"sub": username})
    
    return ResponseModel(
        code=200,
        message="令牌刷新成功",
        data={
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "Bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }
    )


@router.post("/logout", response_model=ResponseModel)
async def logout():
    """User logout endpoint."""
    return ResponseModel(code=200, message="登出成功")


@router.get("/me", response_model=ResponseModel)
async def get_me(current_user: UserResponse = Depends(get_current_user)):
    """Get current user info."""
    return ResponseModel(code=200, message="获取成功", data=current_user)
