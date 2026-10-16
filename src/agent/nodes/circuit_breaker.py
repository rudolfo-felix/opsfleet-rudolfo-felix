"""FinOps Circuit Breaker Node for LangGraph agent.

Halts query execution gracefully when retry_count reaches the maximum limit (<= 2 retries),
producing a friendly executive briefing without throwing unhandled tracebacks.
"""

import logging
from typing import Any

from src.agent.state import AgentState
from src.guardrails.pii import sanitize_text

logger = logging.getLogger(__name__)


def circuit_breaker(state: AgentState) -> dict[str, Any]:
    """Gracefully terminate cyclic self-correction after 2 failed attempts."""
    raw_error = state.get("error_feedback") or "Execution failed to converge on a valid result."
    last_error = sanitize_text(raw_error)
    retries = state.get("retry_count", 2)

    logger.error(
        f"Circuit breaker tripped after {retries} retries. "
        "Halting query execution to preserve FinOps call budget."
    )

    report = (
        "## ⚠️ Analytical Query Notice\n\n"
        f"**Self-Correction Limit Reached:** The assistant attempted {retries} automated corrections "
        "but was unable to complete the query successfully.\n\n"
        f"**Diagnostic Details:**\n```\n{last_error}\n```\n\n"
        "**Recommended Next Steps:**\n"
        "- Verify whether the date range specified has transactional data in the store.\n"
        "- Check the spelling of specific category, department, or brand names.\n"
        "- Try asking a broader or rephrased question.\n\n"
        "*FinOps Guardrail: Zero additional tokens or costs were incurred.*"
    )

    return {
        "executive_report": report,
    }
