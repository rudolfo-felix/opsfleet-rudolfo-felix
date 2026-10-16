"""Shared pytest fixtures for the Retail Data Assistant test suite.

Includes:
- mock_gemini_response: Simulates Gemini SDK generation output.
- sample_agent_state: StateGraph TypedDict state conforming to RFC-001.
- mock_bq_rows: Realistic sample rows for thelook_ecommerce orders and order_items.
"""

from typing import Any
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def sample_agent_state() -> dict[str, Any]:
    """Provide a valid sample AgentState dictionary conforming to RFC-001 §2.2."""
    return {
        "user_query": "What is our net revenue for Calvin Klein in Q1 2026?",
        "user_id": "marcus_category_director",
        "allowed_brands": ["Calvin Klein"],
        "current_sql": "SELECT SUM(sale_price) FROM `bigquery-public-data.thelook_ecommerce.order_items` WHERE status NOT IN ('Cancelled', 'Returned') AND brand = 'Calvin Klein'",
        "sql_history": [],
        "error_feedback": None,
        "retry_count": 0,
        "query_results": [{"brand": "Calvin Klein", "net_revenue": 142500.50, "order_count": 1820}],
        "sanitized_results": [
            {"brand": "Calvin Klein", "net_revenue": 142500.50, "order_count": 1820}
        ],
        "executive_report": (
            "## 1. Executive Summary\n"
            "Calvin Klein delivered $142.5K in Net Revenue across 1,820 orders in Q1.\n\n"
            "## 2. Key Metrics & Tabular Breakdown\n"
            "| Brand | Net Revenue | Orders |\n"
            "|---|---|---|\n"
            "| Calvin Klein | $142,500.50 | 1,820 |\n\n"
            "## 3. Strategic Observations & Action Items\n"
            "- Protect core inventory velocity heading into Q2."
        ),
        "requires_confirmation": False,
        "confirmation_status": None,
        "token_usage": {"prompt_tokens": 320, "completion_tokens": 150, "total_tokens": 470},
    }


@pytest.fixture
def mock_gemini_response():
    """Mock Gemini SDK generation response with text and usage metadata."""

    def _create_response(text: str, prompt_tokens: int = 150, candidates_tokens: int = 80):
        mock_resp = MagicMock()
        mock_resp.text = text
        mock_resp.usage_metadata = MagicMock()
        mock_resp.usage_metadata.prompt_token_count = prompt_tokens
        mock_resp.usage_metadata.candidates_token_count = candidates_tokens
        mock_resp.usage_metadata.total_token_count = prompt_tokens + candidates_tokens
        return mock_resp

    return _create_response


@pytest.fixture
def mock_bq_rows() -> list[dict[str, Any]]:
    """Provide realistic sample rows simulating BigQuery thelook_ecommerce data."""
    return [
        {
            "order_id": 1001,
            "user_id": 501,
            "status": "Complete",
            "gender": "F",
            "created_at": "2026-01-15 10:20:00",
            "num_of_item": 2,
            "sale_price": 89.99,
            "brand": "Calvin Klein",
            "category": "Jeans",
            "email": "customer1@example.com",
            "first_name": "Alice",
            "last_name": "Smith",
            "ip_address": "192.168.1.10",
        },
        {
            "order_id": 1002,
            "user_id": 502,
            "status": "Shipped",
            "gender": "M",
            "created_at": "2026-01-16 14:10:00",
            "num_of_item": 1,
            "sale_price": 120.00,
            "brand": "Tommy Hilfiger",
            "category": "Jackets",
            "email": "customer2@example.com",
            "first_name": "Bob",
            "last_name": "Jones",
            "ip_address": "192.168.1.25",
        },
        {
            "order_id": 1003,
            "user_id": 503,
            "status": "Cancelled",
            "gender": "F",
            "created_at": "2026-01-17 09:05:00",
            "num_of_item": 1,
            "sale_price": 45.00,
            "brand": "Calvin Klein",
            "category": "Underwear",
            "email": "customer3@example.com",
            "first_name": "Carol",
            "last_name": "Brown",
            "ip_address": "192.168.1.50",
        },
    ]
