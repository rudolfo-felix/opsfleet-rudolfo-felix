"""OpenTelemetry GenAI Telemetry & FinOps Token Accounting Engine.

Operationalizes:
- ADR-0002 (Open Standards Observability & Langfuse OSS Readiness)
- Invariant 1 (2-Minute Evaluator Rule with In-Memory and Logging Fallback)
- Invariant 4 (FinOps 2-5 LLM Calls Budget per Turn)
- Invariant 9 (Defensive PII Isolation in Span Attributes & Events)
- CNCF OpenTelemetry GenAI Semantic Conventions (gen_ai.*)
"""

import functools
import logging
import time
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import Status, StatusCode

from src.config import get_settings
from src.guardrails.pii import (
    ADDRESS_COLUMNS,
    CUSTOMER_NAME_COLUMNS,
    EMAIL_COLUMNS,
    IP_COLUMNS,
    TOKEN_ADDRESS,
    TOKEN_EMAIL,
    TOKEN_IP,
    TOKEN_NAME,
    sanitize_text,
)

logger = logging.getLogger(__name__)

# Global singleton exporter and provider for in-process telemetry capture
_IN_MEMORY_EXPORTER: InMemorySpanExporter | None = None
_TRACER_PROVIDER: TracerProvider | None = None


def get_in_memory_exporter() -> InMemorySpanExporter:
    """Retrieve or initialize the global InMemorySpanExporter for testing and telemetry audits."""
    global _IN_MEMORY_EXPORTER
    if _IN_MEMORY_EXPORTER is None:
        _IN_MEMORY_EXPORTER = InMemorySpanExporter()
    return _IN_MEMORY_EXPORTER


def reset_tracer() -> None:
    """Clear in-memory span exporter state for test isolation."""
    exporter = get_in_memory_exporter()
    exporter.clear()


def get_tracer(service_name: str = "thelook-retail-assistant") -> trace.Tracer:
    """Get or configure the global OpenTelemetry Tracer."""
    global _TRACER_PROVIDER, _IN_MEMORY_EXPORTER
    if _TRACER_PROVIDER is None:
        resource = Resource.create({"service.name": service_name})
        _TRACER_PROVIDER = TracerProvider(resource=resource)
        _IN_MEMORY_EXPORTER = get_in_memory_exporter()
        _TRACER_PROVIDER.add_span_processor(SimpleSpanProcessor(_IN_MEMORY_EXPORTER))
        try:
            trace.set_tracer_provider(_TRACER_PROVIDER)
        except Exception:
            pass

    return _TRACER_PROVIDER.get_tracer(service_name)


@dataclass
class FinOpsTracker:
    """Session and turn-level token, call count, and latency accountant.

    Enforces Vlad Bondarenko's FinOps directive: 2-5 LLM calls per analytical query.
    """

    user_id: str = "default_user"
    session_id: str = "default_session"
    query_type: str = "analytical"  # "analytical" or "non_analytical"
    total_llm_calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    node_latencies: dict[str, float] = field(default_factory=dict)

    def record_tokens(self, prompt: int = 0, completion: int = 0) -> None:
        """Record input and output tokens consumed."""
        self.prompt_tokens += max(0, prompt)
        self.completion_tokens += max(0, completion)

    def record_call(self, count: int = 1) -> None:
        """Increment total LLM invocation counter."""
        self.total_llm_calls += max(0, count)

    def record_latency(self, node_name: str, duration_sec: float) -> None:
        """Record latency duration for a specific execution node."""
        self.node_latencies[node_name] = round(
            self.node_latencies.get(node_name, 0.0) + max(0.0, duration_sec), 4
        )

    @property
    def total_tokens(self) -> int:
        """Calculate total tokens consumed across turn."""
        return self.prompt_tokens + self.completion_tokens

    @property
    def cumulative_latency(self) -> float:
        """Calculate total execution time across all recorded nodes."""
        return round(sum(self.node_latencies.values()), 4)

    def assert_budget(self, max_calls: int = 5) -> tuple[bool, str]:
        """Verify whether turn LLM call counts adhere to the FinOps budget.

        - Analytical queries: expect 2-5 calls (1 Gen + 0-2 Self-Correct + 1 Synthesize).
        - Non-analytical operations (help, reports): expect 0-1 calls.
        """
        if self.query_type == "analytical":
            if 2 <= self.total_llm_calls <= max_calls:
                return (
                    True,
                    f"Turn call budget respected: {self.total_llm_calls} calls (budget: 2-{max_calls}).",
                )
            return (
                False,
                f"Turn call budget violated: {self.total_llm_calls} calls (expected 2-{max_calls}).",
            )
        else:
            if self.total_llm_calls <= 1:
                return (
                    True,
                    f"Non-analytical turn call budget respected: {self.total_llm_calls} calls (max: 1).",
                )
            return (
                False,
                f"Non-analytical turn exceeded expected calls: {self.total_llm_calls} calls.",
            )

    def to_summary_dict(self) -> dict[str, Any]:
        """Generate structured summary dictionary for CLI rendering and reporting."""
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "query_type": self.query_type,
            "total_llm_calls": self.total_llm_calls,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "cumulative_latency_sec": self.cumulative_latency,
            "node_latencies": dict(self.node_latencies),
        }


def _sanitize_span_attributes(attributes: dict[str, Any] | None) -> dict[str, Any]:
    """Sanitize all attributes using column-name matching and regex PII scrubbing."""
    if not attributes:
        return {}
    clean: dict[str, Any] = {}
    for key, val in attributes.items():
        lower_key = key.lower()
        # 1. Column-name based scrubbing
        if lower_key in CUSTOMER_NAME_COLUMNS:
            clean[key] = TOKEN_NAME
        elif lower_key in EMAIL_COLUMNS:
            clean[key] = TOKEN_EMAIL
        elif lower_key in IP_COLUMNS:
            clean[key] = TOKEN_IP
        elif lower_key in ADDRESS_COLUMNS:
            clean[key] = TOKEN_ADDRESS
        elif isinstance(val, str):
            clean[key] = sanitize_text(val)
        elif isinstance(val, (int, float, bool)):
            clean[key] = val
        elif isinstance(val, (list, tuple)):
            clean[key] = [sanitize_text(str(x)) if isinstance(x, str) else x for x in val]
        else:
            clean[key] = sanitize_text(str(val))
    return clean


@contextmanager
def start_genai_span(
    name: str,
    operation_name: str = "generate_content",
    model_name: str | None = None,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    attributes: dict[str, Any] | None = None,
    tracker: FinOpsTracker | None = None,
):
    """Context manager for CNCF GenAI Semantic Convention spans (`gen_ai.*`).

    Sets:
    - gen_ai.system = "gemini"
    - gen_ai.request.model
    - gen_ai.response.model
    - gen_ai.operation.name
    - gen_ai.usage.prompt_tokens & gen_ai.usage.input_tokens (dual aliasing)
    - gen_ai.usage.completion_tokens & gen_ai.usage.output_tokens (dual aliasing)
    - gen_ai.usage.total_tokens
    - duration_seconds
    """
    tracer = get_tracer()
    resolved_model = model_name or get_settings().model_name
    start_time = time.perf_counter()

    with tracer.start_as_current_span(name) as span:
        # 1. Standard GenAI Semantic Conventions
        span.set_attribute("gen_ai.system", "gemini")
        span.set_attribute("gen_ai.request.model", resolved_model)
        span.set_attribute("gen_ai.response.model", resolved_model)
        span.set_attribute("gen_ai.operation.name", operation_name)

        # 2. Token Usage with dual-key aliasing for broad collector compatibility
        p_tok = max(0, prompt_tokens)
        c_tok = max(0, completion_tokens)
        span.set_attribute("gen_ai.usage.prompt_tokens", p_tok)
        span.set_attribute("gen_ai.usage.input_tokens", p_tok)
        span.set_attribute("gen_ai.usage.completion_tokens", c_tok)
        span.set_attribute("gen_ai.usage.output_tokens", c_tok)
        span.set_attribute("gen_ai.usage.total_tokens", p_tok + c_tok)

        # 3. Sanitized custom attributes (Invariant 9 PII defense)
        sanitized_attrs = _sanitize_span_attributes(attributes)
        for k, v in sanitized_attrs.items():
            span.set_attribute(k, v)

        try:
            yield span
            span.set_status(Status(StatusCode.OK))
        except Exception as exc:
            span.set_status(Status(StatusCode.ERROR, sanitize_text(str(exc))))
            span.record_exception(exc)
            raise
        finally:
            duration = round(time.perf_counter() - start_time, 4)
            span.set_attribute("duration_seconds", duration)
            if tracker is not None:
                tracker.record_latency(name, duration)
                tracker.record_tokens(prompt=p_tok, completion=c_tok)


def trace_node(node_name: str, tracker: FinOpsTracker | None = None) -> Callable[..., Any]:
    """Decorator or context manager wrapping LangGraph agent nodes with OTel tracing."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = get_tracer()
            span_name = f"agent.{node_name}"
            start_time = time.perf_counter()

            with tracer.start_as_current_span(span_name) as span:
                span.set_attribute("agent.node_name", node_name)
                try:
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as exc:
                    if type(exc).__name__ == "GraphInterrupt":
                        span.set_attribute("agent.interrupted", True)
                        span.add_event("graph.interrupt")
                        raise
                    span.set_status(Status(StatusCode.ERROR, sanitize_text(str(exc))))
                    span.record_exception(exc)
                    raise
                finally:
                    duration = round(time.perf_counter() - start_time, 4)
                    span.set_attribute("duration_seconds", duration)
                    if tracker is not None:
                        tracker.record_latency(node_name, duration)

        return wrapper

    return decorator
