"""Self-correction reflection node for LangGraph agent.

Increments the retry counter and prepares diagnostic error feedback for the generation node.
"""

import logging
from typing import Any

from src.agent.state import AgentState

logger = logging.getLogger(__name__)


def self_correct(state: AgentState) -> dict[str, Any]:
    """Increment retry count while preserving error feedback for the generation node."""
    current_retries = state.get("retry_count", 0)
    new_retries = current_retries + 1

    logger.warning(
        f"Initiating self-correction attempt {new_retries}/2. "
        f"Diagnostic reason: {state.get('error_feedback', 'Unknown error')[:80]}..."
    )

    return {
        "retry_count": new_retries,
    }
