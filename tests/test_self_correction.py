"""Unit tests for LangGraph SQL execution, self-correction loop, circuit breaker, and intent routing."""

from unittest.mock import MagicMock

from src.agent.graph import (
    create_retail_agent_graph,
    evaluate_execution,
    route_intent,
)
from src.agent.nodes.circuit_breaker import circuit_breaker
from src.agent.nodes.execute_sql import ZERO_ROWS_DIAGNOSTIC, execute_sql
from src.agent.nodes.self_correct import self_correct
from src.agent.state import create_initial_state
from src.bq.exceptions import BigQueryClientError


def test_intent_classifier_routing():
    """Verify zero-LLM regex intent classifier routes correctly."""
    # Analytical queries
    state_analytics = create_initial_state("What was our Net Revenue last month?")
    assert route_intent(state_analytics) == "generate_sql"

    state_analytics_orders = create_initial_state("Show total orders by department")
    assert route_intent(state_analytics_orders) == "generate_sql"

    # Report management / destructive commands (OPS-007 HITL isolation)
    state_delete = create_initial_state("Please delete report #4")
    assert route_intent(state_delete) == "reports"

    state_saved = create_initial_state("Show my saved reports")
    assert route_intent(state_saved) == "reports"

    # General help / greeting
    state_help = create_initial_state("help")
    assert route_intent(state_help) == "help"

    state_hello = create_initial_state("hello")
    assert route_intent(state_hello) == "help"


def test_execute_sql_success_rows():
    """Verify execute_sql with rows >= 1 populates results and clears error_feedback."""
    mock_client = MagicMock()
    mock_client.query_to_dicts.return_value = [
        {"category": "Jeans", "net_revenue": 1420.50},
        {"category": "Sweaters", "net_revenue": 980.20},
    ]

    state = create_initial_state("Sales by category")
    state["current_sql"] = (
        "SELECT category, SUM(sale_price) AS net_revenue FROM order_items GROUP BY 1"
    )

    update = execute_sql(state, client=mock_client)

    assert update["query_results"] is not None
    assert len(update["query_results"]) == 2
    assert update["error_feedback"] is None

    # Verify evaluate_execution routes to sanitize_pii gate
    state.update(update)
    assert evaluate_execution(state) == "sanitize_pii"


def test_execute_sql_zero_rows_mitigation3_diagnostic():
    """Verify empty query output populates Mitigation 3 diagnostic feedback."""
    mock_client = MagicMock()
    mock_client.query_to_dicts.return_value = []  # Empty results

    state = create_initial_state("Sales for nonexistent brand")
    state["current_sql"] = "SELECT * FROM products WHERE brand = 'nonexistent'"
    state["retry_count"] = 0

    update = execute_sql(state, client=mock_client)

    assert update["query_results"] == []
    assert update["error_feedback"] == ZERO_ROWS_DIAGNOSTIC
    assert "Common retail causes in thelook_ecommerce" in update["error_feedback"]

    # Verify evaluate_execution routes to self_correct on retry_count < 2
    state.update(update)
    assert evaluate_execution(state) == "self_correct"


def test_execute_sql_compiler_error_capture():
    """Verify compiler and syntax errors are safely captured without throwing tracebacks."""
    mock_client = MagicMock()
    mock_client.query_to_dicts.side_effect = BigQueryClientError(
        "Unrecognized name: invalid_col at [1:10]"
    )

    state = create_initial_state("Invalid query")
    state["current_sql"] = "SELECT invalid_col FROM orders"

    update = execute_sql(state, client=mock_client)

    assert update["query_results"] is None
    assert "BigQuery error: Unrecognized name: invalid_col" in update["error_feedback"]

    state.update(update)
    assert evaluate_execution(state) == "self_correct"


def test_self_correct_node_increments_retry_count():
    """Verify self_correct increments retry_count accurately."""
    state = create_initial_state("Test query")
    state["retry_count"] = 0
    state["error_feedback"] = "Syntax error"

    update1 = self_correct(state)
    assert update1["retry_count"] == 1

    state["retry_count"] = 1
    update2 = self_correct(state)
    assert update2["retry_count"] == 2


def test_circuit_breaker_hard_cap_at_two_retries():
    """Verify circuit breaker triggers at retry_count >= 2 and halts execution gracefully."""
    state = create_initial_state("Persistent failing query")
    state["retry_count"] = 2
    state["error_feedback"] = "Column 'non_existent' not found in table 'orders'"

    # Router must choose circuit_breaker
    assert evaluate_execution(state) == "circuit_breaker"

    # Node must generate user-friendly report
    update = circuit_breaker(state)
    assert "executive_report" in update
    report = update["executive_report"]

    assert "⚠️ Analytical Query Notice" in report
    assert "Self-Correction Limit Reached" in report
    assert "Column 'non_existent' not found" in report
    assert "FinOps Guardrail" in report


def test_stategraph_assembly_and_intent_invocations():
    """Verify StateGraph compiles and handles help and reports intents cleanly."""
    graph = create_retail_agent_graph()

    # 1. Test Help Intent
    state_help = create_initial_state("help")
    result_help = graph.invoke(state_help)
    assert "TheLook Retail Analytics Assistant" in result_help["executive_report"]

    # 2. Test Reports HITL Intent
    state_reports = create_initial_state("Delete report #2")
    result_reports = graph.invoke(state_reports)
    assert result_reports["requires_confirmation"] is True
    assert "Report management requested" in result_reports["executive_report"]
