"""OpenTelemetry Observability and FinOps Accounting package for TheLook Retail Assistant.

Operationalizes ADR-0002 (Open Standards Telemetry) and Invariant 4 (FinOps 2-5 Call Budget).
"""

from src.telemetry.tracer import (
    FinOpsTracker,
    get_in_memory_exporter,
    get_tracer,
    reset_tracer,
    start_genai_span,
    trace_node,
)

__all__ = [
    "FinOpsTracker",
    "get_in_memory_exporter",
    "get_tracer",
    "reset_tracer",
    "start_genai_span",
    "trace_node",
]
