"""结构化日志配置 - P0 修复：CROSS-003"""

import logging
import json
import sys
from datetime import datetime
from typing import Optional, Dict, Any
import uuid
import traceback


class StructuredFormatter(logging.Formatter):
    """
    JSON 格式化日志 - 修复 CROSS-003
    
    输出格式:
    {
        "timestamp": "2026-03-22T10:00:00.000Z",
        "level": "INFO",
        "message": "请求处理完成",
        "request_id": "uuid-xxxx-xxxx",
        "service": "rag-service",
        "user_id": "user123",
        "duration_ms": 150,
        ...
    }
    """
    
    def __init__(
        self,
        service_name: str = "rag-service",
        include_extra: bool = True
    ):
        super().__init__()
        self.service_name = service_name
        self.include_extra = include_extra
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "service": self.service_name,
            "logger": record.name,
            "location": f"{record.pathname}:{record.lineno}"
        }
        
        # 添加 request_id
        request_id = getattr(record, 'request_id', None)
        if request_id:
            log_data["request_id"] = request_id
        
        # 添加 user_id
        user_id = getattr(record, 'user_id', None)
        if user_id:
            log_data["user_id"] = user_id
        
        # 添加额外字段
        if self.include_extra:
            for key, value in record.__dict__.items():
                if key not in {
                    'name', 'msg', 'args', 'created', 'filename', 'funcName',
                    'levelname', 'levelno', 'lineno', 'module', 'msecs',
                    'pathname', 'process', 'processName', 'relativeCreated',
                    'stack_info', 'exc_info', 'thread', 'threadName',
                    'request_id', 'user_id', 'service'
                }:
                    try:
                        json.dumps(value)  # 检查是否可 JSON 序列化
                        log_data[key] = value
                    except (TypeError, ValueError):
                        log_data[key] = str(value)
        
        # 添加异常信息
        if record.exc_info:
            log_data["exc_info"] = True
            log_data["traceback"] = self.formatException(record.exc_info)
            log_data["exception_type"] = record.exc_info[0].__name__ if record.exc_info[0] else None
            log_data["exception_message"] = str(record.exc_info[1]) if record.exc_info[1] else None
        
        return json.dumps(log_data, ensure_ascii=False, default=str)


class RequestLogFilter:
    """
    请求日志过滤器 - 添加 request_id 和 user_id
    """
    
    def __init__(self, request_id: Optional[str] = None, user_id: Optional[str] = None):
        self.request_id = request_id or str(uuid.uuid4())
        self.user_id = user_id
    
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = self.request_id
        record.user_id = self.user_id
        return True


def setup_structured_logging(
    level: int = logging.INFO,
    service_name: str = "rag-service",
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    配置结构化日志
    
    用法:
    logger = setup_structured_logging()
    
    # 带 request_id 的日志
    from contextvars import ContextVar
    request_id_var: ContextVar[str] = ContextVar('request_id', default='')
    
    async def handler(request):
        request_id = str(uuid.uuid4())
        token = request_id_var.set(request_id)
        try:
            logger.info("处理请求")
        finally:
            request_id_var.reset(token)
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # 清除现有处理器
    root_logger.handlers.clear()
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(StructuredFormatter(service_name=service_name))
    root_logger.addHandler(console_handler)
    
    # 文件处理器（可选）
    if log_file:
        import os
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(StructuredFormatter(service_name=service_name))
        root_logger.addHandler(file_handler)
    
    return root_logger


def get_logger(name: str, request_id: Optional[str] = None) -> logging.LoggerAdapter:
    """
    获取带 request_id 的日志适配器
    
    用法:
    logger = get_logger(__name__, request_id="req-123")
    logger.info("处理中...")
    """
    logger = logging.getLogger(name)
    extra = {"request_id": request_id or str(uuid.uuid4())}
    return logging.LoggerAdapter(logger, extra)


# ==================== 请求日志中间件 ====================
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import time


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    请求日志中间件 - 自动记录每个请求
    
    修复 CROSS-003: 错误日志信息不足
    """
    
    def __init__(self, app, logger: Optional[logging.Logger] = None):
        super().__init__(app)
        self.logger = logger or logging.getLogger("request_logger")
    
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())
        
        # 将 request_id 添加到请求状态
        request.state.request_id = request_id
        
        # 开始时间
        start_time = time.time()
        
        # 创建带 request_id 的日志适配器
        logger_adapter = get_logger(__name__, request_id)
        
        try:
            # 记录请求开始
            logger_adapter.info(
                f"请求开始：{request.method} {request.url.path}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "query": str(request.query_params) if request.query_params else None,
                    "client_ip": request.client.host if request.client else None
                }
            )
            
            # 处理请求
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录响应
            logger_adapter.info(
                f"请求完成：{request.method} {request.url.path}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "process_time_ms": round(process_time * 1000, 2),
                    "client_ip": request.client.host if request.client else None
                }
            )
            
            # 添加 request_id 到响应头
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            
            # 记录异常
            logger_adapter.error(
                f"请求失败：{request.method} {request.url.path}",
                exc_info=True,
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                    "process_time_ms": round(process_time * 1000, 2),
                    "client_ip": request.client.host if request.client else None
                }
            )
            raise


# ==================== 全局请求 ID 上下文 ====================
from contextvars import ContextVar

request_id_context: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id_context: ContextVar[Optional[str]] = ContextVar('user_id', default=None)


def get_current_request_id() -> Optional[str]:
    """获取当前请求 ID"""
    return request_id_context.get()


def get_current_user_id() -> Optional[str]:
    """获取当前用户 ID"""
    return user_id_context.get()


def set_request_context(request_id: str, user_id: Optional[str] = None):
    """设置请求上下文"""
    request_id_context.set(request_id)
    if user_id:
        user_id_context.set(user_id)


class ContextLogger(logging.LoggerAdapter):
    """
    自动从上下文获取 request_id 的日志适配器
    """
    
    def process(self, msg, kwargs):
        extra = kwargs.get('extra', {})
        extra['request_id'] = get_current_request_id()
        user_id = get_current_user_id()
        if user_id:
            extra['user_id'] = user_id
        kwargs['extra'] = extra
        return msg, kwargs


def get_context_logger(name: str) -> ContextLogger:
    """获取上下文日志适配器"""
    return ContextLogger(logging.getLogger(name), {})
