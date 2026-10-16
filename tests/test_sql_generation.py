"""Unit tests for LangGraph state schema, prompt engine, and generate_sql node."""

from unittest.mock import MagicMock

from src.agent.nodes.generate_sql import generate_sql
from src.agent.prompts import (
    build_system_prompt,
    build_user_prompt,
    strip_markdown_fences,
)
from src.agent.state import AgentState, create_initial_state
from src.config import Settings


def test_agent_state_initialization_defaults():
    """Verify create_initial_state initializes all 14 attributes with expected types."""
    state = create_initial_state(
        user_query="What was our Net Revenue last month?",
        user_id="exec_1",
        session_id="sess_123",
        allowed_brands=["Calvin Klein"],
    )

    # Context & session
    assert state["user_query"] == "What was our Net Revenue last month?"
    assert state["user_id"] == "exec_1"
    assert state["session_id"] == "sess_123"
    assert state["allowed_brands"] == ["Calvin Klein"]

    # Iteration & self-correction
    assert state["current_sql"] == ""
    assert state["sql_history"] == []
    assert state["error_feedback"] is None
    assert state["retry_count"] == 0

    # Data & Results
    assert state["query_results"] is None
    assert state["sanitized_results"] is None

    # HITL oversight
    assert state["requires_confirmation"] is False
    assert state["confirmation_status"] is None

    # Report & FinOps
    assert state["executive_report"] is None
    assert state["total_llm_calls"] == 0
    assert state["tokens_consumed"] == 0


def test_system_prompt_contains_ontology_and_schema():
    """Verify system prompt contains retail ontology formulas and table schemas."""
    prompt = build_system_prompt()

    # Schema elements
    assert "bigquery-public-data.thelook_ecommerce.orders" in prompt
    assert "bigquery-public-data.thelook_ecommerce.order_items" in prompt
    assert "bigquery-public-data.thelook_ecommerce.products" in prompt
    assert "bigquery-public-data.thelook_ecommerce.users" in prompt

    # ONT-001 Ontology rules
    assert "status NOT IN ('Cancelled', 'Returned')" in prompt
    assert "SAFE_DIVIDE" in prompt
    assert "TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAY)" in prompt


def test_system_prompt_conditional_brand_scoping():
    """Verify brand scoping rules are injected when allowed_brands is present."""
    prompt_scoped = build_system_prompt(allowed_brands=["Calvin Klein", "Nike"])
    assert "Enterprise Brand Scoping Guardrail" in prompt_scoped
    assert "'Calvin Klein', 'Nike'" in prompt_scoped
    assert "DO NOT hallucinate a brand column on `users`" in prompt_scoped

    prompt_unscoped = build_system_prompt(allowed_brands=[])
    assert "Enterprise Brand Scoping Guardrail" not in prompt_unscoped


def test_user_prompt_with_and_without_error_feedback():
    """Verify user prompt integrates diagnostic feedback during self-correction."""
    prompt_simple = build_user_prompt("Show sales by state")
    assert "Executive Request: Show sales by state" in prompt_simple
    assert "Diagnostic Self-Correction Feedback" not in prompt_simple

    prompt_corrected = build_user_prompt(
        user_query="Show sales by state",
        error_feedback="Query returned 0 rows because status filter was misspelled",
        previous_sql="SELECT * FROM orders WHERE status = 'Complet'",
    )
    assert "Diagnostic Self-Correction Feedback" in prompt_corrected
    assert "SELECT * FROM orders WHERE status = 'Complet'" in prompt_corrected
    assert "Query returned 0 rows because status filter was misspelled" in prompt_corrected


def test_strip_markdown_fences():
    """Verify robust stripping of markdown code fences, comments, and semicolons."""
    sql1 = "```sql\nSELECT * FROM orders;\n```"
    assert strip_markdown_fences(sql1) == "SELECT * FROM orders"

    sql2 = "```SQL\nSELECT 1;\n```"
    assert strip_markdown_fences(sql2) == "SELECT 1"

    sql3 = "```\nSELECT order_id FROM order_items;\n```"
    assert strip_markdown_fences(sql3) == "SELECT order_id FROM order_items"

    sql4 = "SELECT * FROM users"
    assert strip_markdown_fences(sql4) == "SELECT * FROM users"


def test_generate_sql_node_execution():
    """Verify generate_sql invokes Gemini, sanitizes output, and updates state."""
    mock_response = MagicMock()
    mock_response.text = """```sql
SELECT
    DATE_TRUNC(created_at, MONTH) AS month,
    ROUND(SUM(sale_price), 2) AS net_revenue
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE oi.status NOT IN ('Cancelled', 'Returned')
GROUP BY 1
ORDER BY 1 DESC;
```"""
    mock_usage = MagicMock()
    mock_usage.total_token_count = 145
    mock_response.usage_metadata = mock_usage

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    mock_settings = Settings(
        gemini_api_key="mock_key_1234567890",
        model_name="gemini-2.5-flash",
    )

    initial_state = create_initial_state("What is our monthly Net Revenue?")
    update = generate_sql(initial_state, client=mock_client, settings=mock_settings)

    # 1. Returned update dictionary
    assert "current_sql" in update
    assert "sql_history" in update
    assert "total_llm_calls" in update
    assert "tokens_consumed" in update

    # 2. Markdown fence stripping & table qualification
    sql = update["current_sql"]
    assert "```" not in sql
    assert "`bigquery-public-data.thelook_ecommerce.orders`" in sql
    assert "`bigquery-public-data.thelook_ecommerce.order_items`" in sql

    # 3. History tracking
    assert len(update["sql_history"]) == 1
    assert update["sql_history"][0] == sql

    # 4. Call count and token accounting
    assert update["total_llm_calls"] == 1
    assert update["tokens_consumed"] == 145


def test_generate_sql_chains_history_and_calls():
    """Verify subsequent self-correction calls append to history and increment calls."""
    mock_response = MagicMock()
    mock_response.text = "SELECT 1"
    mock_response.usage_metadata = MagicMock(total_token_count=50)

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    mock_settings = Settings(
        gemini_api_key="mock_key_1234567890",
        model_name="gemini-2.5-flash",
    )

    state = AgentState(
        user_query="Retry query",
        user_id="user_1",
        session_id="sess_1",
        allowed_brands=[],
        current_sql="SELECT 0",
        sql_history=["SELECT 0"],
        error_feedback="Compiler error",
        retry_count=1,
        query_results=None,
        sanitized_results=None,
        requires_confirmation=False,
        confirmation_status=None,
        executive_report=None,
        total_llm_calls=1,
        tokens_consumed=120,
    )

    update = generate_sql(state, client=mock_client, settings=mock_settings)

    assert update["total_llm_calls"] == 2
    assert update["tokens_consumed"] == 170
    assert len(update["sql_history"]) == 2
    assert update["sql_history"] == ["SELECT 0", "SELECT 1"]
