"""Unit and integration tests for Golden Knowledge Bucket and BigQueryRunner export (OPS-011)."""

from unittest.mock import MagicMock, patch

from src.agent.nodes.generate_sql import generate_sql
from src.agent.prompts import build_user_prompt
from src.agent.state import create_initial_state
from src.bq.client import BigQueryClient, BigQueryRunner
from src.knowledge.golden_bucket import (
    CANONICAL_TRIOS,
    get_golden_bucket,
)


def test_bigquery_runner_alias_and_parity():
    """Verify that BigQueryRunner is cleanly exported as a subclass of BigQueryClient and supports None dataset_id."""
    assert issubclass(BigQueryRunner, BigQueryClient)
    assert BigQueryRunner.__name__ == "BigQueryRunner"

    # Test initialization with optional dataset_id=None (matching Alex Freidman snippet)
    mock_client = MagicMock()
    runner = BigQueryRunner(dataset_id=None, client=mock_client)
    assert runner.dataset_id == "bigquery-public-data.thelook_ecommerce"


def test_golden_bucket_catalog_integrity():
    """Verify that the Golden Knowledge Bucket contains all 5 canonical historical trios."""
    bucket = get_golden_bucket()
    trios = bucket.get_all_trios()
    assert len(trios) == 5
    assert len(CANONICAL_TRIOS) == 5

    expected_ids = {
        "TRIO-001-STATE-SPEND",
        "TRIO-002-CHURN-ANALYSIS",
        "TRIO-003-Q1-EXECUTIVE-REPORT",
        "TRIO-004-PRODUCT-PERFORMANCE",
        "TRIO-005-CATALOG-DISCOVERY",
    }
    actual_ids = {t.id for t in trios}
    assert actual_ids == expected_ids

    for trio in trios:
        assert len(trio.question) > 10
        assert "SELECT" in trio.sql_query
        assert "## Executive Summary" in trio.executive_briefing
        assert len(trio.tags) >= 4
        assert len(trio.business_domain) > 5


def test_golden_bucket_lexical_retrieval():
    """Verify that the lexical retrieval engine matches the canonical assessment prompts accurately."""
    bucket = get_golden_bucket()

    # 1. State underspending
    t1 = bucket.retrieve_relevant_trio("Why are the users for state X underspending? And how does it compare to state Y?")
    assert t1 is not None
    assert t1.id == "TRIO-001-STATE-SPEND"

    # 2. Churn spike
    t2 = bucket.retrieve_relevant_trio("Why did our churn rate spike last month?")
    assert t2 is not None
    assert t2.id == "TRIO-002-CHURN-ANALYSIS"

    # 3. Q1 Report & Q2 Action Items
    t3 = bucket.retrieve_relevant_trio("Create a report for Q1 including insights and action items for Q2.")
    assert t3 is not None
    assert t3.id == "TRIO-003-Q1-EXECUTIVE-REPORT"

    # 4. Product performance comparison
    t4 = bucket.retrieve_relevant_trio("Compare performance of product X and Y, and why do they perform differently")
    assert t4 is not None
    assert t4.id == "TRIO-004-PRODUCT-PERFORMANCE"

    # 5. Database structure
    t5 = bucket.retrieve_relevant_trio("What data is available in the database, and what can we do with it?")
    assert t5 is not None
    assert t5.id == "TRIO-005-CATALOG-DISCOVERY"


def test_golden_bucket_threshold_filtering():
    """Verify that unrelated out-of-domain and low-specificity queries return None."""
    bucket = get_golden_bucket()
    # Unrelated query with zero retail overlap
    unrelated = bucket.retrieve_relevant_trio("What is the recipe for baking chocolate brownies?")
    assert unrelated is None

    empty = bucket.retrieve_relevant_trio("")
    assert empty is None

    # Low-specificity retail queries should not falsely match complex exemplars
    assert bucket.retrieve_relevant_trio("How many customers do we have?") is None
    assert bucket.retrieve_relevant_trio("show orders last month") is None
    assert bucket.retrieve_relevant_trio("latest orders") is None

    # Strong keyword and multi-word phrase queries should match
    t_rev = bucket.retrieve_relevant_trio("net revenue")
    assert t_rev is not None
    assert t_rev.id == "TRIO-003-Q1-EXECUTIVE-REPORT"


def test_build_user_prompt_with_golden_trio():
    """Verify that build_user_prompt formats the retrieved golden trio correctly."""
    bucket = get_golden_bucket()
    trio = bucket.get_trio_by_id("TRIO-001-STATE-SPEND")
    assert trio is not None

    prompt = build_user_prompt(
        user_query="How does California spend compare to Texas?",
        golden_trio=trio,
    )

    assert "Executive Request: How does California spend compare to Texas?" in prompt
    assert "### Relevant Historical Reference (Golden Knowledge Trio):" in prompt
    assert f"Analyst Domain: {trio.business_domain}" in prompt
    assert trio.question in prompt
    assert "Canonical Reference GoogleSQL:" in prompt
    assert "SELECT" in prompt


@patch("src.agent.nodes.generate_sql.genai.Client")
def test_generate_sql_injects_and_records_trio(mock_genai_client_class):
    """Verify that generate_sql injects the retrieved trio and records its ID in state."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "SELECT * FROM `bigquery-public-data.thelook_ecommerce.orders` LIMIT 10"
    mock_usage = MagicMock()
    mock_usage.total_token_count = 150
    mock_response.usage_metadata = mock_usage
    mock_client.models.generate_content.return_value = mock_response

    state = create_initial_state(
        user_query="Why are the users for state California underspending compared to New York?",
    )

    result = generate_sql(state=state, client=mock_client)

    assert result["retrieved_trio_id"] == "TRIO-001-STATE-SPEND"
    assert result["current_sql"] == "SELECT * FROM `bigquery-public-data.thelook_ecommerce.orders` LIMIT 10"
    assert result["total_llm_calls"] == 1
    assert result["tokens_consumed"] == 150
