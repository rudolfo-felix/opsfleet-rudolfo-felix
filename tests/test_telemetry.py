"""Tests for OpenTelemetry GenAI Telemetry & FinOps Token Accounting (OPS-008).

Validates:
1. Standard CNCF GenAI Semantic Conventions (gen_ai.*).
2. Dual-key aliasing for token usage (prompt_tokens/input_tokens, completion_tokens/output_tokens).
3. Defensive PII scrubbing in span attributes and event messages.
4. Node latency profiling and duration tracking.
5. FinOpsTracker budget enforcement (2-5 LLM calls per turn for analytical queries).
6. Test isolation via reset_tracer() and InMemorySpanExporter.
"""

import time
from typing import Any

import pytest

from src.telemetry.tracer import (
    FinOpsTracker,
    get_in_memory_exporter,
    reset_tracer,
    start_genai_span,
    trace_node,
)


@pytest.fixture(autouse=True)
def setup_telemetry_isolation():
    """Ensure every test begins with a fresh in-memory exporter."""
    reset_tracer()
    yield
    reset_tracer()


def test_tracer_span_creation_and_genai_semantic_conventions():
    """Verify GenAI semantic conventions and dual-key token aliasing in emitted spans."""
    tracker = FinOpsTracker(user_id="exec_sarah", session_id="sess_123")

    with start_genai_span(
        name="test.gemini_call",
        operation_name="generate_content",
        model_name="gemini-2.5-flash",
        prompt_tokens=142,
        completion_tokens=58,
        attributes={"query_type": "analytical_revenue"},
        tracker=tracker,
    ) as span:
        time.sleep(0.01)
        assert span.is_recording()

    exporter = get_in_memory_exporter()
    spans = exporter.get_finished_spans()
    assert len(spans) == 1

    s = spans[0]
    assert s.name == "test.gemini_call"
    attrs = s.attributes

    # 1. CNCF GenAI Semantic Conventions
    assert attrs["gen_ai.system"] == "gemini"
    assert attrs["gen_ai.request.model"] == "gemini-2.5-flash"
    assert attrs["gen_ai.response.model"] == "gemini-2.5-flash"
    assert attrs["gen_ai.operation.name"] == "generate_content"

    # 2. Dual-key token usage aliasing
    assert attrs["gen_ai.usage.prompt_tokens"] == 142
    assert attrs["gen_ai.usage.input_tokens"] == 142
    assert attrs["gen_ai.usage.completion_tokens"] == 58
    assert attrs["gen_ai.usage.output_tokens"] == 58
    assert attrs["gen_ai.usage.total_tokens"] == 200

    # 3. Latency
    assert attrs["duration_seconds"] > 0
    assert s.status.is_ok

    # 4. Tracker aggregation
    assert tracker.prompt_tokens == 142
    assert tracker.completion_tokens == 58
    assert tracker.total_tokens == 200
    assert tracker.cumulative_latency > 0


def test_pii_sanitization_in_span_attributes():
    """Verify customer PII is strictly scrubbed before injection into span attributes."""
    attributes = {
        "user_email": "customer.john.doe@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "client_ip": "192.168.1.100",
        "order_amount": 129.50,
        "is_vip": True,
        "notes": "Contact user at john.doe@corp.net regarding order issue",
    }

    with start_genai_span(
        name="test.pii_scrub_span",
        operation_name="generate_content",
        attributes=attributes,
    ):
        pass

    spans = get_in_memory_exporter().get_finished_spans()
    assert len(spans) == 1
    attrs = spans[0].attributes

    # Check that sensitive customer data is redacted
    assert attrs["user_email"] == "[EMAIL_REDACTED]"
    assert attrs["first_name"] == "[NAME_REDACTED]"
    assert attrs["last_name"] == "[NAME_REDACTED]"
    assert attrs["client_ip"] == "[IP_REDACTED]"
    assert "[EMAIL_REDACTED]" in attrs["notes"]
    assert "john.doe@corp.net" not in attrs["notes"]

    # Non-PII scalar attributes preserved
    assert attrs["order_amount"] == 129.50
    assert attrs["is_vip"] is True


def test_trace_node_decorator_success_and_error():
    """Verify trace_node captures node latencies and errors cleanly."""
    tracker = FinOpsTracker(user_id="exec_marcus")

    @trace_node("execute_sql", tracker=tracker)
    def successful_node(state: dict[str, Any]) -> dict[str, Any]:
        time.sleep(0.005)
        return {"rows": 42}

    @trace_node("failing_node", tracker=tracker)
    def failing_node(state: dict[str, Any]) -> dict[str, Any]:
        raise ValueError("Invalid column 'credit_card' in SQL query")

    # 1. Success execution
    res = successful_node({"user_query": "Test"})
    assert res["rows"] == 42
    assert "execute_sql" in tracker.node_latencies
    assert tracker.node_latencies["execute_sql"] > 0

    # 2. Failing execution
    with pytest.raises(ValueError, match="Invalid column"):
        failing_node({})

    spans = get_in_memory_exporter().get_finished_spans()
    assert len(spans) == 2

    # Check successful span
    s_ok = next(s for s in spans if s.name == "agent.execute_sql")
    assert s_ok.status.is_ok
    assert s_ok.attributes["agent.node_name"] == "execute_sql"
    assert s_ok.attributes["duration_seconds"] > 0

    # Check error span
    s_err = next(s for s in spans if s.name == "agent.failing_node")
    assert not s_err.status.is_ok
    assert s_err.status.status_code.name == "ERROR"
    assert "Invalid column 'credit_card'" in s_err.status.description


def test_finops_budget_tracker_enforcement():
    """Verify Vlad Bondarenko's FinOps directive: 2-5 calls per analytical query."""
    # 1. Analytical query with valid budget (2 calls: 1 SQL gen + 1 synthesis)
    t_valid_2 = FinOpsTracker(query_type="analytical", total_llm_calls=2)
    ok_2, msg_2 = t_valid_2.assert_budget()
    assert ok_2 is True
    assert "respected" in msg_2

    # 2. Analytical query with 1 retry (3 calls: 1 SQL gen + 1 self-correct + 1 synthesis)
    t_valid_3 = FinOpsTracker(query_type="analytical", total_llm_calls=3)
    ok_3, msg_3 = t_valid_3.assert_budget()
    assert ok_3 is True

    # 3. Analytical query with 2 retries (4 calls: 1 SQL gen + 2 self-correct + 1 synthesis)
    t_valid_4 = FinOpsTracker(query_type="analytical", total_llm_calls=4)
    ok_4, msg_4 = t_valid_4.assert_budget()
    assert ok_4 is True

    # 4. Analytical query under-budget (1 call, missing synthesis)
    t_under = FinOpsTracker(query_type="analytical", total_llm_calls=1)
    ok_under, msg_under = t_under.assert_budget()
    assert ok_under is False
    assert "violated" in msg_under

    # 5. Analytical query over-budget (> 5 calls)
    t_over = FinOpsTracker(query_type="analytical", total_llm_calls=6)
    ok_over, msg_over = t_over.assert_budget()
    assert ok_over is False
    assert "violated" in msg_over

    # 6. Non-analytical query (help or reports: 0-1 calls expected)
    t_non_ana_0 = FinOpsTracker(query_type="non_analytical", total_llm_calls=0)
    ok_na_0, _ = t_non_ana_0.assert_budget()
    assert ok_na_0 is True

    t_non_ana_2 = FinOpsTracker(query_type="non_analytical", total_llm_calls=2)
    ok_na_2, msg_na_2 = t_non_ana_2.assert_budget()
    assert ok_na_2 is False
    assert "exceeded" in msg_na_2


def test_finops_summary_dictionary_generation():
    """Verify to_summary_dict() generates expected structured payload."""
    tracker = FinOpsTracker(
        user_id="exec_sarah",
        session_id="session_retail_001",
        query_type="analytical",
    )
    tracker.record_call(2)
    tracker.record_tokens(prompt=250, completion=120)
    tracker.record_latency("generate_sql", 0.45)
    tracker.record_latency("synthesize", 0.82)

    summary = tracker.to_summary_dict()
    assert summary["user_id"] == "exec_sarah"
    assert summary["session_id"] == "session_retail_001"
    assert summary["total_llm_calls"] == 2
    assert summary["prompt_tokens"] == 250
    assert summary["completion_tokens"] == 120
    assert summary["total_tokens"] == 370
    assert summary["cumulative_latency_sec"] == 1.27
    assert summary["node_latencies"]["generate_sql"] == 0.45
    assert summary["node_latencies"]["synthesize"] == 0.82


def test_langgraph_pipeline_emits_telemetry_spans():
    """Verify executing graph operations emits agent node spans into InMemorySpanExporter."""
    from src.agent.graph import create_retail_agent_graph
    from src.agent.state import create_initial_state

    graph = create_retail_agent_graph()

    # Invoke reports flow
    state = create_initial_state("show saved reports")
    result = graph.invoke(state)
    assert "Saved Reports" in result["executive_report"]

    spans = get_in_memory_exporter().get_finished_spans()
    assert len(spans) >= 1
    report_span = next(s for s in spans if s.name == "agent.reports")
    assert report_span.attributes["agent.node_name"] == "reports"
    assert report_span.attributes["duration_seconds"] >= 0
    assert report_span.status.is_ok
