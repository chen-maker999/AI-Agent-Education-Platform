"""Kimi API 重试和熔断机制 - P0 修复：GEN-001"""

import asyncio
import time
from typing import Optional, Callable, Any, Dict
from datetime import datetime
import logging
import json
from enum import Enum

logger = logging.getLogger("kimi_circuit_breaker")


class CircuitState(Enum):
    """熔断器状态"""
    CLOSED = "closed"  # 正常状态
    OPEN = "open"  # 熔断状态
    HALF_OPEN = "half_open"  # 半开状态（尝试恢复）


class CircuitBreakerError(Exception):
    """熔断器异常"""
    pass


class CircuitBreaker:
    """
    熔断器实现 - 修复 GEN-001
    
    功能:
    - 失败次数超过阈值时自动熔断
    - 熔断后经过一段时间自动尝试恢复
    - 半开状态只允许一个请求通过测试
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,  # 失败阈值
        recovery_timeout: int = 60,  # 恢复超时（秒）
        half_open_max_calls: int = 1,  # 半开状态最大调用数
        expected_exceptions: tuple = (Exception,)  # 预期异常类型
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0
        self._lock = asyncio.Lock()
        
        # 统计信息
        self.stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "circuit_opened": 0,
            "circuit_closed": 0
        }
    
    @property
    def state(self) -> CircuitState:
        """获取当前状态"""
        if self._state == CircuitState.OPEN:
            # 检查是否应该尝试恢复
            if time.time() - self._last_failure_time >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                self._half_open_calls = 0
                logger.info("熔断器进入半开状态，尝试恢复")
        return self._state
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        通过熔断器调用函数
        
        状态机:
        CLOSED (正常) -> 失败达阈值 -> OPEN (熔断)
        OPEN (熔断) -> 恢复超时 -> HALF_OPEN (半开)
        HALF_OPEN (半开) -> 成功 -> CLOSED (正常)
        HALF_OPEN (半开) -> 失败 -> OPEN (熔断)
        """
        async with self._lock:
            current_state = self.state
            self.stats["total_calls"] += 1
            
            # OPEN 状态：拒绝调用
            if current_state == CircuitState.OPEN:
                wait_time = self.recovery_timeout - (time.time() - self._last_failure_time)
                raise CircuitBreakerError(
                    f"熔断器开启，拒绝调用。请等待 {wait_time:.1f} 秒后重试"
                )
            
            # HALF_OPEN 状态：限制调用次数
            if current_state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.half_open_max_calls:
                    raise CircuitBreakerError("熔断器半开状态，已达最大调用次数")
                self._half_open_calls += 1
        
        # 执行调用
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise
    
    async def _on_success(self):
        """成功回调"""
        async with self._lock:
            self.stats["successful_calls"] += 1
            self._failure_count = 0
            
            if self._state == CircuitState.HALF_OPEN:
                # 半开状态成功，关闭熔断器
                self._state = CircuitState.CLOSED
                self.stats["circuit_closed"] += 1
                logger.info("熔断器关闭，服务恢复正常")
            
            self._success_count += 1
    
    async def _on_failure(self):
        """失败回调"""
        async with self._lock:
            self.stats["failed_calls"] += 1
            self._failure_count += 1
            self._last_failure_time = time.time()
            
            if self._state == CircuitState.HALF_OPEN:
                # 半开状态失败，重新打开熔断器
                self._state = CircuitState.OPEN
                self.stats["circuit_opened"] += 1
                logger.warning("熔断器重新打开")
            elif self._state == CircuitState.CLOSED:
                # 闭合状态失败，检查是否达到阈值
                if self._failure_count >= self.failure_threshold:
                    self._state = CircuitState.OPEN
                    self.stats["circuit_opened"] += 1
                    logger.warning(f"熔断器打开：失败次数达到阈值 ({self._failure_count}/{self.failure_threshold})")
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            **self.stats,
            "state": self.state.value,
            "failure_count": self._failure_count,
            "failure_threshold": self.failure_threshold
        }


class RetryConfig:
    """重试配置"""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: tuple = (Exception,)
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions


async def retry_with_backoff(
    func: Callable,
    *args,
    config: Optional[RetryConfig] = None,
    logger: Optional[logging.Logger] = None,
    **kwargs
) -> Any:
    """
    指数退避重试 - 修复 GEN-001
    
    策略:
    - 第 1 次重试：等待 1-2 秒
    - 第 2 次重试：等待 2-4 秒
    - 第 3 次重试：等待 4-8 秒
    - ...
    
    公式：delay = min(base_delay * (exponential_base ^ attempt) + jitter, max_delay)
    """
    if config is None:
        config = RetryConfig()
    
    last_exception = None
    attempt = 0
    
    while attempt <= config.max_retries:
        try:
            return await func(*args, **kwargs)
        except config.retryable_exceptions as e:
            last_exception = e
            
            if attempt >= config.max_retries:
                break
            
            # 计算延迟时间
            delay = config.base_delay * (config.exponential_base ** attempt)
            
            if config.jitter:
                import random
                delay = delay * (0.5 + random.random())  # 添加 50%-150% 的抖动
            
            delay = min(delay, config.max_delay)
            
            if logger:
                logger.warning(
                    f"调用失败，{delay:.1f}秒后重试 (attempt={attempt + 1}/{config.max_retries}), error={str(e)}"
                )
            else:
                print(f"调用失败，{delay:.1f}秒后重试 (attempt={attempt + 1}/{config.max_retries}), error={str(e)}")
            
            await asyncio.sleep(delay)
            attempt += 1
    
    raise last_exception


# ==================== Kimi API 专用封装 ====================
class KimiAPIClient:
    """
    Kimi API 客户端 - 带重试和熔断
    
    修复 GEN-001: Kimi API 调用无重试和熔断机制
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.moonshot.cn/v1",
        circuit_breaker: Optional[CircuitBreaker] = None,
        retry_config: Optional[RetryConfig] = None
    ):
        from common.core.config import settings
        
        self.api_key = api_key or settings.KIMI_API_KEY
        self.base_url = base_url
        
        self.circuit_breaker = circuit_breaker or CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            expected_exceptions=(Exception,)
        )
        
        self.retry_config = retry_config or RetryConfig(
            max_retries=3,
            base_delay=1.0,
            max_delay=30.0,
            retryable_exceptions=(Exception,)
        )
        
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "retried_requests": 0
        }
    
    async def chat_completion(
        self,
        messages: list,
        model: str = "moonshot-v1-128k",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        """
        调用 Kimi API 进行对话 - 带重试和熔断
        """
        async def _call_api():
            from common.integration.kimi import get_kimi_response
            
            # 使用现有的 Kimi 集成
            return await get_kimi_response(
                prompt=messages[-1]["content"] if messages else "",
                system_prompt=messages[0]["content"] if len(messages) > 1 else "你是一位专业的助手",
                temperature=temperature,
                max_tokens=max_tokens
            )
        
        try:
            # 通过熔断器调用
            result = await self.circuit_breaker.call(_call_api)
            self.stats["successful_requests"] += 1
            return result
        except CircuitBreakerError as e:
            self.stats["failed_requests"] += 1
            logger.error(f"熔断器阻止调用：{e}")
            raise
        except Exception as e:
            self.stats["failed_requests"] += 1
            logger.error(f"API 调用失败：{e}", exc_info=True)
            raise
        finally:
            self.stats["total_requests"] += 1
    
    async def chat_completion_with_retry(
        self,
        messages: list,
        model: str = "moonshot-v1-128k",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        """
        调用 Kimi API 进行对话 - 带重试和熔断
        """
        async def _call_with_retry():
            return await retry_with_backoff(
                self.chat_completion,
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                config=self.retry_config,
                logger=logger,
                **kwargs
            )
        
        try:
            result = await self.circuit_breaker.call(_call_with_retry)
            self.stats["successful_requests"] += 1
            return result
        except Exception as e:
            self.stats["failed_requests"] += 1
            raise
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            **self.stats,
            "circuit_breaker": self.circuit_breaker.get_stats()
        }


# ==================== 降级策略 ====================
async def kimi_fallback_response(query: str) -> str:
    """
    Kimi API 降级响应 - 当 API 不可用时的本地模板响应
    """
    fallback_templates = [
        f"抱歉，暂时无法连接到智能助手。关于您的问题「{query}」，建议您：\n1. 查看相关教材章节\n2. 搜索技术文档\n3. 向老师或同学请教",
        f"系统暂时无法提供详细解答。关于「{query}」，您可以尝试重新表述问题或稍后再试。",
        f"服务暂时不可用。问题「{query}」的解答需要更多上下文，建议您提供更多详细信息。"
    ]
    
    import random
    return random.choice(fallback_templates)


async def call_kimi_with_fallback(
    prompt: str,
    system_prompt: str = "你是一位专业的助手",
    use_fallback: bool = True,
    **kwargs
) -> str:
    """
    调用 Kimi API 带降级策略
    
    优先级:
    1. Kimi API (带重试和熔断)
    2. 本地降级响应
    """
    client = KimiAPIClient()
    
    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        return await client.chat_completion_with_retry(
            messages=messages,
            **kwargs
        )
    except Exception as e:
        logger.error(f"Kimi API 调用失败，使用降级响应：{e}")
        
        if use_fallback:
            return await kimi_fallback_response(prompt)
        else:
            raise
