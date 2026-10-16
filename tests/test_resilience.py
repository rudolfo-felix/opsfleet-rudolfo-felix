"""Unit tests for the rate-limit exponential backoff and jitter decorator."""

from unittest.mock import patch

import pytest

from src.agent.resilience import (
    calculate_backoff_delay,
    is_rate_limit_error,
    retry_with_backoff,
)


class DummyRateLimitError(Exception):
    """Simulate Google AI Studio HTTP 429 RESOURCE_EXHAUSTED exception."""

    def __init__(self, message="429 Resource has been exhausted (e.g. check quota)."):
        super().__init__(message)
        self.status_code = 429


def test_is_rate_limit_error_detection():
    """Verify accurate detection of various rate-limit exception shapes."""
    assert is_rate_limit_error(DummyRateLimitError())
    assert is_rate_limit_error(Exception("HTTP 429 Too Many Requests"))
    assert is_rate_limit_error(Exception("RESOURCE_EXHAUSTED: quota exceeded"))
    assert not is_rate_limit_error(ValueError("Invalid argument"))
    assert not is_rate_limit_error(KeyError("missing_key"))


def test_calculate_backoff_delay():
    """Verify exponential delay calculation with factor=2.0."""
    d0 = calculate_backoff_delay(attempt=0, initial_delay=1.0, factor=2.0, jitter=False)
    assert d0 == 1.0

    d1 = calculate_backoff_delay(attempt=1, initial_delay=1.0, factor=2.0, jitter=False)
    assert d1 == 2.0

    d2 = calculate_backoff_delay(attempt=2, initial_delay=1.0, factor=2.0, jitter=False)
    assert d2 == 4.0

    # With jitter, delay should remain in valid positive bounds
    d_jitter = calculate_backoff_delay(attempt=1, initial_delay=1.0, factor=2.0, jitter=True)
    assert 1.5 <= d_jitter <= 2.5


@patch("time.sleep", return_value=None)
def test_retry_success_after_rate_limit(mock_sleep):
    """Verify retry succeeds after transient 429 rate limit."""
    call_count = 0
    retries_recorded = []

    def on_retry_hook(attempt, delay, exc):
        retries_recorded.append((attempt, delay))

    @retry_with_backoff(
        max_retries=3,
        initial_delay=0.1,
        factor=2.0,
        jitter=False,
        on_retry=on_retry_hook,
    )
    def flaky_llm_call():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise DummyRateLimitError("429 RESOURCE_EXHAUSTED")
        return "Generated SQL result"

    result = flaky_llm_call()
    assert result == "Generated SQL result"
    assert call_count == 2
    assert len(retries_recorded) == 1
    assert retries_recorded[0][0] == 1
    assert mock_sleep.call_count == 1


@patch("time.sleep", return_value=None)
def test_retry_exhausted_raises_exception(mock_sleep):
    """Verify decorator raises when max_retries limit is exceeded."""
    call_count = 0

    @retry_with_backoff(
        max_retries=2,
        initial_delay=0.1,
        factor=2.0,
        jitter=False,
    )
    def persistent_failing_call():
        nonlocal call_count
        call_count += 1
        raise DummyRateLimitError("429 Quota Exceeded")

    with pytest.raises(DummyRateLimitError):
        persistent_failing_call()

    # Initial call + 2 retries = 3 calls
    assert call_count == 3
    assert mock_sleep.call_count == 2


@patch("time.sleep", return_value=None)
def test_non_retryable_error_raises_immediately(mock_sleep):
    """Verify non-rate-limit errors bypass retry logic completely."""
    call_count = 0

    @retry_with_backoff(max_retries=3)
    def syntax_error_call():
        nonlocal call_count
        call_count += 1
        raise ValueError("Invalid SQL syntax")

    with pytest.raises(ValueError):
        syntax_error_call()

    assert call_count == 1
    assert mock_sleep.call_count == 0


@pytest.mark.asyncio
async def test_async_retry_with_backoff():
    """Verify async function support under rate-limiting."""
    call_count = 0

    with patch("asyncio.sleep", return_value=None) as mock_async_sleep:

        @retry_with_backoff(max_retries=2, initial_delay=0.1, factor=2.0, jitter=False)
        async def async_llm_call():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise DummyRateLimitError("429 Too Many Requests")
            return "Async response"

        result = await async_llm_call()
        assert result == "Async response"
        assert call_count == 2
        assert mock_async_sleep.call_count == 1
