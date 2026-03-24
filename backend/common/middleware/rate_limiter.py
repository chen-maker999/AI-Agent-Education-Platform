"""请求限流中间件 - 基于 Redis 的令牌桶算法"""

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional, Dict, Tuple
from datetime import datetime
import time
import redis
import json

try:
    from common.logging_config import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


# ==================== 配置 ====================
class RateLimitConfig:
    """限流配置"""
    # Redis 配置
    REDIS_HOST = "localhost"
    REDIS_PORT = 6379
    REDIS_DB = 1  # 使用 DB1 存储限流数据
    REDIS_PASSWORD = None

    # 默认限流配置
    DEFAULT_REQUESTS = 60  # 默认每分钟 60 请求
    DEFAULT_WINDOW = 60  # 默认时间窗口 60 秒

    # 令牌桶配置
    BUCKET_CAPACITY = 100  # 桶容量
    BUCKET_REFILL_RATE = 10  # 每秒补充 10 个令牌

    # 限流键前缀
    KEY_PREFIX = "ratelimit:"
    BUCKET_KEY_PREFIX = "ratelimit:bucket:"


# ==================== 令牌桶实现 ====================
class TokenBucket:
    """
    令牌桶限流器

    算法原理:
    - 桶中有固定数量的令牌
    - 每秒按固定速率补充令牌
    - 每个请求消耗一个令牌
    - 桶空时拒绝请求

    优势:
    - 允许突发流量 (桶中有令牌时)
    - 平滑限流
    - 支持分布式 (基于 Redis)
    """

    def __init__(self, redis_client: redis.Redis, capacity: int = 100, refill_rate: float = 10.0):
        self.redis = redis_client
        self.capacity = capacity
        self.refill_rate = refill_rate  # 每秒补充的令牌数

    def _get_bucket_key(self, identifier: str) -> str:
        """生成桶键"""
        return f"{RateLimitConfig.BUCKET_KEY_PREFIX}{identifier}"

    def _get_bucket_state(self, key: str) -> Tuple[float, float]:
        """获取桶状态 (tokens, last_update)"""
        data = self.redis.get(key)
        if data:
            state = json.loads(data)
            return state["tokens"], state["last_update"]
        return self.capacity, time.time()

    def _set_bucket_state(self, key: str, tokens: float, last_update: float, ttl: int = 3600):
        """设置桶状态"""
        data = json.dumps({"tokens": tokens, "last_update": last_update})
        self.redis.setex(key, ttl, data)

    def consume(self, identifier: str, tokens: int = 1) -> Tuple[bool, float, Dict]:
        """
        消费令牌

        Args:
            identifier: 限流标识 (如 user_id, ip)
            tokens: 需要消费的令牌数

        Returns:
            (allowed, remaining_tokens, info)
        """
        key = self._get_bucket_key(identifier)
        now = time.time()

        # 获取当前状态
        current_tokens, last_update = self._get_bucket_state(key)

        # 计算补充的令牌数
        elapsed = now - last_update
        new_tokens = min(self.capacity, current_tokens + elapsed * self.refill_rate)

        # 检查是否有足够令牌
        if new_tokens >= tokens:
            # 允许请求
            new_tokens -= tokens
            self._set_bucket_state(key, new_tokens, now)
            return True, new_tokens, {
                "remaining": int(new_tokens),
                "reset": int(now + (self.capacity - new_tokens) / self.refill_rate),
                "limit": self.capacity
            }
        else:
            # 拒绝请求，更新状态
            self._set_bucket_state(key, new_tokens, now)
            wait_time = (tokens - new_tokens) / self.refill_rate
            return False, new_tokens, {
                "remaining": 0,
                "reset": int(now + wait_time),
                "limit": self.capacity,
                "retry_after": int(wait_time)
            }


# ==================== 滑动窗口限流实现 ====================
class SlidingWindowRateLimiter:
    """
    滑动窗口限流器

    算法原理:
    - 记录每个时间窗口内的请求数
    - 使用滑动窗口避免边界问题
    - 支持分布式 (基于 Redis)

    优势:
    - 精确控制请求数
    - 避免固定窗口的边界问题
    """

    def __init__(self, redis_client: redis.Redis, max_requests: int = 60, window_seconds: int = 60):
        self.redis = redis_client
        self.max_requests = max_requests
        self.window = window_seconds

    def _get_key(self, identifier: str) -> str:
        """生成键"""
        return f"{RateLimitConfig.KEY_PREFIX}{identifier}"

    def is_allowed(self, identifier: str) -> Tuple[bool, Dict]:
        """
        检查请求是否允许

        Returns:
            (allowed, info)
        """
        key = self._get_key(identifier)
        now = time.time()
        window_start = now - self.window

        # 使用 pipeline 保证原子性
        pipe = self.redis.pipeline()

        # 删除窗口外的请求
        pipe.zremrangebyscore(key, 0, window_start)

        # 计算当前窗口内的请求数
        pipe.zcard(key)

        # 添加当前请求
        pipe.zadd(key, {str(now): now})

        # 设置过期时间
        pipe.expire(key, self.window + 1)

        # 执行
        results = pipe.execute()
        current_requests = results[1]

        if current_requests < self.max_requests:
            return True, {
                "remaining": self.max_requests - current_requests - 1,
                "reset": int(now + self.window),
                "limit": self.max_requests
            }
        else:
            return False, {
                "remaining": 0,
                "reset": int(now + self.window),
                "limit": self.max_requests,
                "retry_after": self.window
            }


# ==================== 限流中间件 ====================
class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    请求限流中间件

    支持两种限流模式:
    1. 令牌桶：允许突发流量
    2. 滑动窗口：精确控制请求数

    限流维度:
    - IP 地址
    - 用户 ID (如果已认证)
    - API 路径
    """

    def __init__(
        self,
        app,
        enabled: bool = True,
        mode: str = "token_bucket",  # "token_bucket" or "sliding_window"
        default_requests: int = 60,
        default_window: int = 60,
        whitelist: Optional[list] = None,
        blacklist: Optional[list] = None,
        custom_limits: Optional[Dict[str, Dict]] = None
    ):
        super().__init__(app)
        self.enabled = enabled
        self.mode = mode
        self.default_requests = default_requests
        self.default_window = default_window
        self.whitelist = set(whitelist or [])
        self.blacklist = set(blacklist or [])
        self.custom_limits = custom_limits or {}

        # 初始化 Redis 连接
        self.redis: Optional[redis.Redis] = None
        self.token_bucket: Optional[TokenBucket] = None
        self.sliding_window: Optional[SlidingWindowRateLimiter] = None

        self._connect_redis()

    def _connect_redis(self):
        """连接 Redis"""
        try:
            self.redis = redis.Redis(
                host=RateLimitConfig.REDIS_HOST,
                port=RateLimitConfig.REDIS_PORT,
                db=RateLimitConfig.REDIS_DB,
                password=RateLimitConfig.REDIS_PASSWORD,
                decode_responses=True,
                socket_connect_timeout=5
            )
            self.redis.ping()

            # 初始化限流器
            self.token_bucket = TokenBucket(
                self.redis,
                capacity=RateLimitConfig.BUCKET_CAPACITY,
                refill_rate=RateLimitConfig.BUCKET_REFILL_RATE
            )
            self.sliding_window = SlidingWindowRateLimiter(
                self.redis,
                max_requests=self.default_requests,
                window_seconds=self.default_window
            )

            logger.info("[RateLimit] Redis 连接成功，限流中间件已启用")
        except Exception as e:
            logger.warning(f"[RateLimit] Redis 连接失败，限流功能不可用：{e}")
            self.redis = None

    def _get_identifier(self, request: Request) -> str:
        """获取限流标识"""
        # 优先使用用户 ID
        user_id = request.headers.get("X-User-ID")
        if user_id:
            return f"user:{user_id}"

        # 使用 IP 地址
        client_ip = request.client.host if request.client else "unknown"
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()

        return f"ip:{client_ip}"

    def _get_custom_limit(self, path: str) -> Optional[Dict]:
        """获取自定义限流配置"""
        for pattern, config in self.custom_limits.items():
            if path.startswith(pattern):
                return config
        return None

    def _is_whitelisted(self, identifier: str) -> bool:
        """检查是否在白名单"""
        return identifier in self.whitelist

    def _is_blacklisted(self, identifier: str) -> bool:
        """检查是否在黑名单"""
        return identifier in self.blacklist

    async def dispatch(self, request: Request, call_next) -> Response:
        """处理请求"""
        if not self.enabled or not self.redis:
            return await call_next(request)

        identifier = self._get_identifier(request)
        path = request.url.path

        # 检查白名单
        if self._is_whitelisted(identifier):
            return await call_next(request)

        # 检查黑名单
        if self._is_blacklisted(identifier):
            return JSONResponse(
                status_code=403,
                content={
                    "code": 403,
                    "message": "IP 已被列入黑名单",
                    "data": {"identifier": identifier}
                }
            )

        # 获取限流配置
        custom_limit = self._get_custom_limit(path)
        max_requests = custom_limit.get("requests", self.default_requests) if custom_limit else self.default_requests
        window = custom_limit.get("window", self.default_window) if custom_limit else self.default_window

        # 执行限流检查
        if self.mode == "token_bucket":
            # 更新令牌桶配置
            self.token_bucket.capacity = custom_limit.get("capacity", RateLimitConfig.BUCKET_CAPACITY) if custom_limit else RateLimitConfig.BUCKET_CAPACITY
            self.token_bucket.refill_rate = custom_limit.get("refill_rate", RateLimitConfig.BUCKET_REFILL_RATE) if custom_limit else RateLimitConfig.BUCKET_REFILL_RATE

            allowed, remaining, info = self.token_bucket.consume(identifier)
        else:
            # 更新滑动窗口配置
            self.sliding_window.max_requests = max_requests
            self.sliding_window.window = window

            allowed, info = self.sliding_window.is_allowed(identifier)
            remaining = info.get("remaining", 0)

        # 构建响应
        response = await call_next(request)

        # 添加限流头
        response.headers["X-RateLimit-Limit"] = str(info.get("limit", max_requests))
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(info.get("reset", 0))

        if not allowed:
            retry_after = info.get("retry_after", 60)
            response.headers["Retry-After"] = str(retry_after)

            return JSONResponse(
                status_code=429,
                content={
                    "code": 429,
                    "message": "请求过于频繁，请稍后再试",
                    "data": {
                        "identifier": identifier,
                        "path": path,
                        "limit": info.get("limit"),
                        "retry_after": retry_after
                    }
                },
                headers=response.headers
            )

        return response


# ==================== 限流装饰器 ====================
def rate_limit(requests: int = 60, window: int = 60):
    """
    限流装饰器

    用法:
        @rate_limit(requests=10, window=60)
        async def my_endpoint():
            ...
    """
    def decorator(func):
        func._rate_limit = {"requests": requests, "window": window}
        return func
    return decorator


# ==================== 工具函数 ====================
def get_rate_limit_info(identifier: str, redis_client: Optional[redis.Redis] = None) -> Dict:
    """获取限流信息"""
    if not redis_client:
        return {"error": "Redis not connected"}

    try:
        # 获取令牌桶状态
        bucket_key = f"{RateLimitConfig.BUCKET_KEY_PREFIX}{identifier}"
        data = redis_client.get(bucket_key)
        if data:
            state = json.loads(data)
            return {
                "identifier": identifier,
                "tokens": state["tokens"],
                "last_update": state["last_update"],
                "capacity": RateLimitConfig.BUCKET_CAPACITY
            }

        return {
            "identifier": identifier,
            "tokens": RateLimitConfig.BUCKET_CAPACITY,
            "last_update": None,
            "capacity": RateLimitConfig.BUCKET_CAPACITY
        }
    except Exception as e:
        return {"error": str(e)}


async def reset_rate_limit(identifier: str, redis_client: Optional[redis.Redis] = None) -> bool:
    """重置限流状态"""
    if not redis_client:
        return False

    try:
        bucket_key = f"{RateLimitConfig.BUCKET_KEY_PREFIX}{identifier}"
        window_key = f"{RateLimitConfig.KEY_PREFIX}{identifier}"

        redis_client.delete(bucket_key, window_key)
        return True
    except Exception:
        return False


# ==================== FastAPI 路由 ====================
from fastapi import APIRouter

router = APIRouter(prefix="/ratelimit", tags=["Rate Limiting"])


@router.get("/info")
async def get_rate_limit_info_endpoint(identifier: Optional[str] = None):
    """获取限流信息"""
    from backend.main import app
    # 获取中间件
    for middleware in app.user_middleware:
        if isinstance(middleware.cls, RateLimitMiddleware):
            middleware_instance = middleware
            break
    else:
        return {"code": 500, "message": "限流中间件未启用"}

    if not identifier:
        return {"code": 400, "message": "请提供 identifier 参数"}

    info = get_rate_limit_info(identifier, middleware_instance.redis)
    return {"code": 200, "data": info}


@router.post("/reset")
async def reset_rate_limit_endpoint(identifier: str):
    """重置限流状态"""
    from backend.main import app
    for middleware in app.user_middleware:
        if isinstance(middleware.cls, RateLimitMiddleware):
            middleware_instance = middleware
            break
    else:
        return {"code": 500, "message": "限流中间件未启用"}

    success = await reset_rate_limit(identifier, middleware_instance.redis)
    return {"code": 200 if success else 500, "message": "限流状态已重置" if success else "重置失败"}


@router.get("/config")
async def get_rate_limit_config():
    """获取限流配置"""
    return {
        "code": 200,
        "data": {
            "enabled": True,
            "mode": "token_bucket",
            "default": {
                "requests": RateLimitConfig.DEFAULT_REQUESTS,
                "window": RateLimitConfig.DEFAULT_WINDOW
            },
            "token_bucket": {
                "capacity": RateLimitConfig.BUCKET_CAPACITY,
                "refill_rate": RateLimitConfig.BUCKET_REFILL_RATE
            },
            "redis": {
                "host": RateLimitConfig.REDIS_HOST,
                "port": RateLimitConfig.REDIS_PORT,
                "db": RateLimitConfig.REDIS_DB
            }
        }
    }
