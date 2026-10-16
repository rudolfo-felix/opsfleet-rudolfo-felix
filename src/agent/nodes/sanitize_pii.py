"""PII Sanitizer Gate Node for LangGraph agent.

Operationalizes Invariant 9 (PII Scrubbing Gate) and ADR-0005.
Scrubs customer identifiers from raw query results into state["sanitized_results"]
before data reaches the executive report synthesizer.
"""

import logging
from typing import Any

from src.agent.state import AgentState
from src.guardrails.pii import sanitize_records
from src.telemetry.tracer import trace_node

logger = logging.getLogger(__name__)


@trace_node("sanitize_pii")
def sanitize_pii(state: AgentState) -> dict[str, Any]:
    """LangGraph node: scrub customer PII from raw query results into sanitized_results."""
    raw_results = state.get("query_results") or []

    sanitized = sanitize_records(raw_results)

    logger.debug(
        f"PII Sanitizer Gate processed {len(sanitized)} records. "
        "Customer identifiers masked; product catalog titles preserved."
    )

    return {
        "sanitized_results": sanitized,
    }
