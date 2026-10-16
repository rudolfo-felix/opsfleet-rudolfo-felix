"""Resilience module implementing rate limit backoff and jitter for Google AI Studio.

Adheres to Invariant 3 (Rate Limit Resilience) and Invariant 4 (Call Budget Discipline)
by catching HTTP 429 / RESOURCE_EXHAUSTED and backing off gracefully.
"""

import inspect
import logging
import random
import time
from collections.abc import Callable
from functools import wraps
from typing import Any

try:
    from rich.console import Console

    console = Console(stderr=True)
except ImportError:
    console = None

logger = logging.getLogger(__name__)


class RateLimitExhaustedError(Exception):
    """Raised when exponential backoff retries are exhausted on HTTP 429."""

    pass


def is_rate_limit_error(exc: Exception) -> bool:
    """Determine whether an exception represents an HTTP 429 / RESOURCE_EXHAUSTED rate limit."""
    msg = str(exc).lower()

    # Check for HTTP 429 or RESOURCE_EXHAUSTED in message
    if "429" in msg or "resource_exhausted" in msg or "quota" in msg or "rate limit" in msg:
        return True

    # Check status_code or code attribute if available
    status_code = getattr(exc, "status_code", getattr(exc, "code", None))
    if status_code in (429, "RESOURCE_EXHAUSTED"):
        return True

    # Check Google API exception types by name
    exc_type_name = type(exc).__name__
    if exc_type_name in ("ResourceExhausted", "TooManyRequests"):
        return True

    return False


def calculate_backoff_delay(
    attempt: int,
    initial_delay: float = 1.0,
    factor: float = 2.0,
    max_delay: float = 30.0,
    jitter: bool = True,
) -> float:
    """Calculate exponential backoff delay with optional uniform jitter.

    Formula:
        delay = min(max_delay, initial_delay * factor^attempt) +/- jitter
    """
    delay = min(max_delay, initial_delay * (factor**attempt))
    if jitter:
        # Uniform jitter between 0 and 0.5 seconds
        jitter_val = random.uniform(0.0, 0.5)
        # Randomly add or subtract slightly, ensuring delay stays positive
        delay = max(0.1, delay + random.choice([-1, 1]) * (jitter_val / 2.0))
    return round(delay, 2)


def retry_with_backoff(
    func: Callable | None = None,
    *,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    factor: float = 2.0,
    max_delay: float = 30.0,
    jitter: bool = True,
    retryable_exceptions: tuple[type[Exception], ...] | None = None,
    on_retry: Callable[[int, float, Exception], None] | None = None,
):
    """Decorator to retry functions failing due to HTTP 429 / RESOURCE_EXHAUSTED.

    Supports both bare @retry_with_backoff and parameterized @retry_with_backoff(max_retries=5).

    Args:
        func: Optional function when used as bare decorator @retry_with_backoff.
        max_retries: Number of retry attempts before giving up (default: 3).
        initial_delay: Initial delay in seconds (default: 1.0s).
        factor: Multiplicative factor for exponential backoff (default: 2.0).
        max_delay: Ceiling on backoff duration in seconds (default: 30.0s).
        jitter: Whether to add random jitter to mitigate thundering herds (default: True).
        retryable_exceptions: Optional tuple of explicit exception classes to catch.
        on_retry: Optional hook callable(attempt, delay, exception) invoked on each retry.
    """

    def decorator(fn: Callable):
        @wraps(fn)
        def sync_wrapper(*args, **kwargs) -> Any:
            attempt = 0
            while True:
                try:
                    return fn(*args, **kwargs)
                except Exception as exc:
                    # Check if error qualifies as rate limit
                    is_retryable = False
                    if retryable_exceptions and isinstance(exc, retryable_exceptions):
                        is_retryable = True
                    elif is_rate_limit_error(exc):
                        is_retryable = True

                    if not is_retryable or attempt >= max_retries:
                        if is_retryable:
                            logger.error(
                                f"Rate limit retry exhausted after {attempt} attempts for {fn.__name__}."
                            )
                        raise

                    attempt += 1
                    delay = calculate_backoff_delay(
                        attempt=attempt - 1,
                        initial_delay=initial_delay,
                        factor=factor,
                        max_delay=max_delay,
                        jitter=jitter,
                    )

                    # Log user-friendly notification
                    alert_msg = (
                        f"Google AI Studio rate limit reached (HTTP 429). "
                        f"Backing off for {delay}s (Attempt {attempt}/{max_retries})..."
                    )
                    if console:
                        console.print(f"[yellow]{alert_msg}[/yellow]")
                    else:
                        logger.warning(alert_msg)

                    if on_retry:
                        on_retry(attempt, delay, exc)

                    time.sleep(delay)

        @wraps(fn)
        async def async_wrapper(*args, **kwargs) -> Any:
            import asyncio

            attempt = 0
            while True:
                try:
                    return await fn(*args, **kwargs)
                except Exception as exc:
                    is_retryable = False
                    if retryable_exceptions and isinstance(exc, retryable_exceptions):
                        is_retryable = True
                    elif is_rate_limit_error(exc):
                        is_retryable = True

                    if not is_retryable or attempt >= max_retries:
                        if is_retryable:
                            logger.error(
                                f"Rate limit retry exhausted after {attempt} attempts for {fn.__name__}."
                            )
                        raise

                    attempt += 1
                    delay = calculate_backoff_delay(
                        attempt=attempt - 1,
                        initial_delay=initial_delay,
                        factor=factor,
                        max_delay=max_delay,
                        jitter=jitter,
                    )

                    alert_msg = (
                        f"Google AI Studio rate limit reached (HTTP 429). "
                        f"Backing off for {delay}s (Attempt {attempt}/{max_retries})..."
                    )
                    if console:
                        console.print(f"[yellow]{alert_msg}[/yellow]")
                    else:
                        logger.warning(alert_msg)

                    if on_retry:
                        on_retry(attempt, delay, exc)

                    await asyncio.sleep(delay)

        if inspect.iscoroutinefunction(fn):
            return async_wrapper
        return sync_wrapper

    if func is not None:
        return decorator(func)
    return decorator
