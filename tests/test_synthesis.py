"""Unit tests for executive insight synthesis node and PII data boundary."""

from unittest.mock import MagicMock

from src.agent.nodes.synthesize import (
    defensive_scrub_records,
    format_records_as_markdown,
    synthesize,
)
from src.agent.state import create_initial_state
from src.config import Settings


def test_defensive_scrub_records_masks_pii():
    """Verify in-node defensive scrubber replaces customer PII with redacted tokens."""
    raw_records = [
        {
            "id": 1,
            "first_name": "Sarah",
            "last_name": "Connor",
            "email": "sarah.connor@example.com",
            "ip_address": "192.168.1.55",
            "street_address": "123 Main St",
            "total_spend": 450.0,
        }
    ]

    scrubbed = defensive_scrub_records(raw_records)
    assert len(scrubbed) == 1
    row = scrubbed[0]

    assert row["first_name"] == "[NAME_REDACTED]"
    assert row["last_name"] == "[NAME_REDACTED]"
    assert row["email"] == "[EMAIL_REDACTED]"
    assert row["ip_address"] == "[IP_REDACTED]"
    assert row["street_address"] == "[ADDRESS_REDACTED]"
    assert row["total_spend"] == 450.0


def test_format_records_as_markdown():
    """Verify tabular records format cleanly as markdown tables."""
    records = [
        {"category": "Jeans", "net_revenue": 12500.0},
        {"category": "Sweaters", "net_revenue": 8900.0},
    ]
    md = format_records_as_markdown(records)
    assert "| category | net_revenue |" in md
    assert "| Jeans | 12500.0 |" in md
    assert "| Sweaters | 8900.0 |" in md

    empty_md = format_records_as_markdown([])
    assert "Zero records returned" in empty_md


def test_synthesize_produces_three_h2_sections():
    """Verify synthesizer produces briefing strictly structured with 3 H2 sections."""
    mock_report = """## Executive Summary
Net revenue for Q1 reached $452,000, driven predominantly by strong outerware and denim demand across California and Texas.

## Key Findings
| Category | Net Revenue (USD) | Margin % |
|---|---|---|
| Jeans | $145,000 | 44.2% |
| Sweaters | $112,000 | 41.8% |

## Q2 Action Items
1. Increase safety stock on top-performing denim SKUs by 15% before May.
2. Reallocate ad spend toward Texas digital acquisition campaigns."""

    mock_resp = MagicMock()
    mock_resp.text = mock_report
    mock_resp.usage_metadata = MagicMock(total_token_count=210)

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_resp

    mock_settings = Settings(
        gemini_api_key="mock_key_synthesis_test",
        model_name="gemini-2.5-flash",
    )

    state = create_initial_state("What was our Net Revenue by category?")
    state["sanitized_results"] = [
        {"category": "Jeans", "net_revenue": 145000.0},
        {"category": "Sweaters", "net_revenue": 112000.0},
    ]
    state["total_llm_calls"] = 1
    state["tokens_consumed"] = 150

    update = synthesize(state, client=mock_client, settings=mock_settings)

    assert "executive_report" in update
    report = update["executive_report"]

    # Verify all 3 mandated H2 sections
    assert "## Executive Summary" in report
    assert "## Key Findings" in report
    assert "## Q2 Action Items" in report

    # Verify FinOps call accounting increment
    assert update["total_llm_calls"] == 2
    assert update["tokens_consumed"] == 360


def test_synthesize_prefers_sanitized_results_over_raw():
    """Verify synthesizer strictly consumes sanitized_results to uphold PII boundary."""
    mock_resp = MagicMock()
    mock_resp.text = (
        "## Executive Summary\nSummary\n## Key Findings\nFindings\n## Q2 Action Items\nActions"
    )
    mock_resp.usage_metadata = MagicMock(total_token_count=100)

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_resp

    mock_settings = Settings(
        gemini_api_key="mock_key_synthesis_test",
        model_name="gemini-2.5-flash",
    )

    # State with pre-sanitized results
    state = create_initial_state("Customer emails")
    state["sanitized_results"] = [{"user_id": 1, "email": "[EMAIL_REDACTED]", "state": "CA"}]
    state["query_results"] = [{"user_id": 1, "email": "leak@example.com", "state": "CA"}]

    update = synthesize(state, client=mock_client, settings=mock_settings)
    assert update["executive_report"] is not None

    # Inspect prompt contents sent to generate_content
    call_args = mock_client.models.generate_content.call_args
    prompt_sent = call_args.kwargs["contents"]

    assert "[EMAIL_REDACTED]" in prompt_sent
    assert "leak@example.com" not in prompt_sent


def test_synthesize_handles_empty_dataset_gracefully():
    """Verify synthesizer formats empty datasets cleanly with executive context."""
    mock_resp = MagicMock()
    mock_resp.text = """## Executive Summary
No transactions matched the requested timeframe.

## Key Findings
Zero records returned for the query.

## Q2 Action Items
1. Review date parameters with marketing operations."""
    mock_resp.usage_metadata = MagicMock(total_token_count=80)

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_resp

    mock_settings = Settings(
        gemini_api_key="mock_key_synthesis_test",
        model_name="gemini-2.5-flash",
    )

    state = create_initial_state("Sales in Alaska")
    state["sanitized_results"] = []

    update = synthesize(state, client=mock_client, settings=mock_settings)
    report = update["executive_report"]

    assert "## Executive Summary" in report
    assert "## Key Findings" in report
    assert "## Q2 Action Items" in report
