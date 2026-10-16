"""LangGraph AgentState schema and state initialization factory.

Operationalizes ADR-0001 (LangGraph State Machine) and pre-allocates all attributes
required by downstream nodes (OPS-004 through OPS-007) to guarantee zero breaking migrations.
"""

import uuid
from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    """Complete state container for the LangGraph analytical agent workflow.

    Attributes:
        user_query: Natural language executive question entered by the user.
        user_id: Unique identifier for the requesting user/executive.
        session_id: Unique identifier for the conversation session or thread.
        allowed_brands: Multi-tenant brand scoping permissions (e.g. ['Calvin Klein']).
        current_sql: Most recently generated GoogleSQL query string.
        sql_history: Chronological list of all generated SQL iterations for auditing.
        error_feedback: Compiler or 0-rows diagnostic feedback from execution node.
        retry_count: Current number of self-correction retries (capped at <= 2).
        query_results: Raw query execution output dictionaries from BigQuery/DuckDB.
        sanitized_results: PII-redacted query execution output dictionaries (OPS-006).
        requires_confirmation: Flag signaling high-stakes action awaiting HITL approval (OPS-007).
        confirmation_status: User decision on pending HITL action (True/False/None).
        executive_report: Final synthesized Markdown briefing for Sarah (OPS-005).
        total_llm_calls: Monotonically increasing count of LLM API calls in this turn.
        tokens_consumed: Approximate or reported input/output token count for FinOps.
    """

    # Session & Identity Context
    user_query: str
    user_id: str
    session_id: str
    allowed_brands: list[str]

    # SQL Iteration & Self-Correction
    current_sql: str
    sql_history: list[str]
    error_feedback: str | None
    retry_count: int

    # Data & Results
    query_results: list[dict[str, Any]] | None
    sanitized_results: list[dict[str, Any]] | None

    # HITL Oversight (EU AI Act Art. 14)
    requires_confirmation: bool
    confirmation_status: bool | None

    # Reporting & Insights
    executive_report: str | None

    # FinOps Telemetry & Budgets
    total_llm_calls: int
    tokens_consumed: int


def create_initial_state(
    user_query: str,
    user_id: str = "executive_user",
    session_id: str | None = None,
    allowed_brands: list[str] | None = None,
) -> AgentState:
    """Create a pristine AgentState instance with established defaults."""
    return AgentState(
        user_query=user_query,
        user_id=user_id,
        session_id=session_id or str(uuid.uuid4()),
        allowed_brands=allowed_brands or [],
        current_sql="",
        sql_history=[],
        error_feedback=None,
        retry_count=0,
        query_results=None,
        sanitized_results=None,
        requires_confirmation=False,
        confirmation_status=None,
        executive_report=None,
        total_llm_calls=0,
        tokens_consumed=0,
    )
