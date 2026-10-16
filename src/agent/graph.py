"""LangGraph StateGraph Assembler for TheLook Retail Assistant.

Operationalizes ADR-0001 (LangGraph State Machine), Invariant 4 (FinOps 2-5 Call Budget),
and Invariant 11 (Self-Correction Loop capped at <= 2 retries).
"""

import logging
import re
from typing import Any

from langgraph.graph import END, START, StateGraph

from src.agent.nodes.circuit_breaker import circuit_breaker
from src.agent.nodes.execute_sql import execute_sql
from src.agent.nodes.generate_sql import generate_sql
from src.agent.nodes.reports import reports_node
from src.agent.nodes.sanitize_pii import sanitize_pii
from src.agent.nodes.self_correct import self_correct
from src.agent.nodes.synthesize import synthesize
from src.agent.state import AgentState

logger = logging.getLogger(__name__)


def route_intent(state: AgentState) -> str:
    """Zero-LLM deterministic Intent Classifier routing at graph entrypoint."""
    query = state.get("user_query", "").strip()

    # 1. Report management & destructive actions (OPS-007 HITL isolation)
    if (
        re.search(r"\b(delete|remove|clear|drop|purge)\s+.*report\b", query, re.IGNORECASE)
        or re.search(r"\b(saved\s+reports|list\s+reports|view\s+reports|show\s+reports)\b", query, re.IGNORECASE)
        or re.search(r"\b(save|bookmark|store)\s+.*report\b", query, re.IGNORECASE)
        or re.search(r"^\s*(save\s+report|list\s+reports|show\s+saved\s+reports)\s*$", query, re.IGNORECASE)
    ):
        return "reports"

    # 2. General help / greetings
    if re.search(r"^\s*(help|what can you do|commands|\?|hello|hi)\s*$", query, re.IGNORECASE):
        return "help"

    # 3. Default: Analytical retail queries
    return "generate_sql"


def evaluate_execution(state: AgentState) -> str:
    """Conditional router following SQL query execution.

    Directs flow to:
    - self_correct: if an error occurred or 0 rows returned AND retry_count < 2.
    - circuit_breaker: if an error occurred or 0 rows returned AND retry_count >= 2.
    - sanitize_pii: if execution succeeded with rows >= 1 to scrub PII before synthesis.
    """
    if state.get("error_feedback"):
        if state.get("retry_count", 0) < 2:
            return "self_correct"
        return "circuit_breaker"
    return "sanitize_pii"


def help_node(state: AgentState) -> dict[str, Any]:
    """Provide system guidance and capabilities for general user queries."""
    help_text = (
        "## 🛍️ TheLook Retail Analytics Assistant\n\n"
        "I can answer executive questions across sales, profitability, churn, and inventory:\n"
        "- **Net Revenue:** *'What was our Net Revenue by category last quarter?'*\n"
        "- **Brand Margins:** *'Which brands generate our highest gross profit margins?'*\n"
        "- **Customer Churn:** *'How many customers are currently churned?'*\n"
        "- **Saved Reports:** *'Show my saved reports'* or *'Delete report #3'*"
    )
    return {"executive_report": help_text}


def create_retail_agent_graph(checkpointer: Any | None = None) -> Any:
    """Assemble and compile the complete LangGraph StateGraph."""
    workflow = StateGraph(AgentState)

    # Register Nodes
    workflow.add_node("generate_sql", generate_sql)
    workflow.add_node("execute_sql", execute_sql)
    workflow.add_node("self_correct", self_correct)
    workflow.add_node("circuit_breaker", circuit_breaker)
    workflow.add_node("sanitize_pii", sanitize_pii)
    workflow.add_node("synthesize", synthesize)
    workflow.add_node("reports", reports_node)
    workflow.add_node("help", help_node)

    # Entrypoint Intent Routing
    workflow.add_conditional_edges(
        START,
        route_intent,
        {
            "generate_sql": "generate_sql",
            "reports": "reports",
            "help": "help",
        },
    )

    # Core SQL Pipeline & Self-Correction Cycle
    workflow.add_edge("generate_sql", "execute_sql")

    workflow.add_conditional_edges(
        "execute_sql",
        evaluate_execution,
        {
            "self_correct": "self_correct",
            "circuit_breaker": "circuit_breaker",
            "sanitize_pii": "sanitize_pii",
        },
    )

    # Reflection loop back to SQL generator
    workflow.add_edge("self_correct", "generate_sql")

    # PII Sanitizer Gate to Synthesizer
    workflow.add_edge("sanitize_pii", "synthesize")

    # Terminal edges
    workflow.add_edge("circuit_breaker", END)
    workflow.add_edge("synthesize", END)
    workflow.add_edge("reports", END)
    workflow.add_edge("help", END)

    return workflow.compile(checkpointer=checkpointer)
