"""Unit tests for MockDuckDBEngine, GoogleSQL dialect translation, and dual-client fallback."""

import os
from unittest.mock import patch

import pandas as pd
import pytest

from src.bq.client import get_bigquery_client
from src.bq.exceptions import CredentialsMissingError, ReadOnlyQueryViolationError
from src.bq.mock_engine import (
    MockDuckDBEngine,
    generate_synthetic_data,
    translate_googlesql_to_duckdb,
)


def test_dialect_strips_table_qualifications():
    """Verify dialect normalizer strips BigQuery dataset prefixes and backticks."""
    sql = "SELECT * FROM `bigquery-public-data.thelook_ecommerce.orders` WHERE order_id = 1"
    translated = translate_googlesql_to_duckdb(sql)
    assert "`" not in translated
    assert "bigquery-public-data" not in translated
    assert "FROM orders" in translated

    sql2 = "SELECT * FROM thelook_ecommerce.products p JOIN `thelook_ecommerce.order_items` oi ON p.id = oi.product_id"
    translated2 = translate_googlesql_to_duckdb(sql2)
    assert "FROM products p" in translated2
    assert "JOIN order_items oi" in translated2


def test_dialect_translates_temporal_functions():
    """Verify translation of TIMESTAMP_SUB, DATE_SUB, and interval math."""
    sql = "SELECT * FROM orders WHERE created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)"
    translated = translate_googlesql_to_duckdb(sql)
    assert "TIMESTAMP_SUB" not in translated
    assert "- INTERVAL '30' DAY" in translated

    sql_month = (
        "SELECT * FROM orders WHERE created_at >= DATE_SUB(CURRENT_DATE(), INTERVAL '6' MONTH)"
    )
    translated_month = translate_googlesql_to_duckdb(sql_month)
    assert "DATE_SUB" not in translated_month
    assert "- INTERVAL '6' MONTH" in translated_month


def test_dialect_translates_date_trunc_argument_inversion():
    """Verify DATE_TRUNC and TIMESTAMP_TRUNC reverse argument ordering for DuckDB."""
    sql = "SELECT DATE_TRUNC(created_at, MONTH) AS month, COUNT(*) FROM orders GROUP BY 1"
    translated = translate_googlesql_to_duckdb(sql)
    assert "date_trunc('month', created_at)" in translated

    sql2 = "SELECT TIMESTAMP_TRUNC(created_at, DAY) AS day FROM orders"
    translated2 = translate_googlesql_to_duckdb(sql2)
    assert "date_trunc('day', created_at)" in translated2


def test_dialect_translates_safe_divide():
    """Verify SAFE_DIVIDE translation handles both simple and nested aggregation expressions."""
    sql = "SELECT SAFE_DIVIDE(10, 2) AS simple_div"
    translated = translate_googlesql_to_duckdb(sql)
    assert "SAFE_DIVIDE" not in translated
    assert "CAST((10) AS DOUBLE) / NULLIF((2), 0)" in translated

    sql_nested = "SELECT SAFE_DIVIDE(SUM(oi.sale_price) - SUM(p.cost), SUM(oi.sale_price)) AS margin_pct FROM order_items oi"
    translated_nested = translate_googlesql_to_duckdb(sql_nested)
    assert "SAFE_DIVIDE" not in translated_nested
    assert "NULLIF((SUM(oi.sale_price)), 0)" in translated_nested


def test_dialect_translates_countif_and_datetime():
    """Verify translation of COUNTIF to COUNT_IF and CURRENT_DATETIME to CURRENT_TIMESTAMP."""
    sql = (
        "SELECT COUNTIF(status = 'Complete') AS completed, CURRENT_DATETIME() AS cur_dt FROM orders"
    )
    translated = translate_googlesql_to_duckdb(sql)
    assert "COUNT_IF(status = 'Complete')" in translated
    assert "CURRENT_TIMESTAMP" in translated


def test_dialect_normalizes_double_quoted_strings():
    """Verify double quotes in filter expressions are converted to single quotes."""
    sql = 'SELECT * FROM orders WHERE status = "Complete" AND state IN ("CA", "NY")'
    translated = translate_googlesql_to_duckdb(sql)
    assert "status = 'Complete'" in translated
    assert "('CA', 'NY')" in translated


def test_synthetic_fixtures_integrity():
    """Verify synthetic fixtures meet all RFC-OPS-002B and Ticket criteria."""
    fixtures = generate_synthetic_data()

    users = fixtures["users"]
    products = fixtures["products"]
    orders = fixtures["orders"]
    order_items = fixtures["order_items"]

    # 1. Row counts >= 50
    assert len(users) >= 50, f"Expected >=50 users, got {len(users)}"
    assert len(products) >= 50, f"Expected >=50 products, got {len(products)}"
    assert len(orders) >= 50, f"Expected >=50 orders, got {len(orders)}"
    assert len(order_items) >= 50, f"Expected >=50 order_items, got {len(order_items)}"

    # 2. Key required columns present
    assert "ip_address" in users.columns
    assert "email" in users.columns
    assert "brand" in products.columns
    assert "cost" in products.columns
    assert "sale_price" in order_items.columns
    assert "status" in orders.columns
    assert "created_at" in orders.columns

    # 3. Temporal span >= 6 calendar months
    order_dates = pd.to_datetime(orders["created_at"])
    span_days = (order_dates.max() - order_dates.min()).days
    assert span_days >= 180, f"Expected >= 180 days span, got {span_days} days"

    # 4. Geographic diversity >= 3 distinct US states
    distinct_states = users["state"].nunique()
    assert distinct_states >= 3, f"Expected >= 3 states, got {distinct_states}"

    # 5. Order statuses contain expected business values
    statuses = set(orders["status"].unique())
    assert "Complete" in statuses
    assert "Cancelled" in statuses
    assert "Returned" in statuses


def test_mock_engine_query_execution():
    """Verify MockDuckDBEngine executes GoogleSQL queries and returns DataFrames."""
    engine = MockDuckDBEngine()

    # Analytical Net Revenue Query (simulating BigQuery prompt output)
    sql = """
        SELECT
            ROUND(SUM(sale_price), 2) AS net_revenue,
            COUNT(DISTINCT order_id) AS total_orders
        FROM `bigquery-public-data.thelook_ecommerce.order_items`
        WHERE status NOT IN ('Cancelled', 'Returned')
    """
    df = engine.query_to_dataframe(sql)
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert df["net_revenue"].iloc[0] > 0
    assert df["total_orders"].iloc[0] > 0


def test_mock_engine_brand_margins_analytical_query():
    """Verify MockDuckDBEngine executes multi-table join with safe division."""
    engine = MockDuckDBEngine()
    sql = """
        SELECT
            p.brand,
            ROUND(SUM(oi.sale_price), 2) AS total_sales,
            ROUND(SUM(p.cost), 2) AS total_cost,
            ROUND(SAFE_DIVIDE(SUM(oi.sale_price) - SUM(p.cost), SUM(oi.sale_price)), 4) AS gross_margin_pct
        FROM `bigquery-public-data.thelook_ecommerce.order_items` oi
        JOIN `bigquery-public-data.thelook_ecommerce.products` p ON oi.product_id = p.id
        WHERE oi.status = 'Complete'
        GROUP BY p.brand
        ORDER BY total_sales DESC
        LIMIT 5;
    """
    df = engine.query_to_dataframe(sql)
    assert not df.empty
    assert len(df) <= 5
    assert "brand" in df.columns
    assert "gross_margin_pct" in df.columns
    assert df["gross_margin_pct"].iloc[0] is not None


def test_mock_engine_query_to_dicts_serialization():
    """Verify records are serializable and timestamps formatted to ISO strings."""
    engine = MockDuckDBEngine()
    sql = "SELECT order_id, status, created_at FROM orders LIMIT 3"
    dicts = engine.query_to_dicts(sql)
    assert len(dicts) == 3
    for record in dicts:
        assert isinstance(record["order_id"], int)
        assert isinstance(record["created_at"], str)  # ISO formatted


def test_mock_engine_rejects_mutating_sql():
    """Verify security guardrail blocks mutating SQL queries."""
    engine = MockDuckDBEngine()
    with pytest.raises(ReadOnlyQueryViolationError):
        engine.execute_query("DROP TABLE orders")

    with pytest.raises(ReadOnlyQueryViolationError):
        engine.execute_query("DELETE FROM users WHERE id = 1")


def test_get_bigquery_client_force_mock():
    """Verify get_bigquery_client returns MockDuckDBEngine when force_mock=True."""
    client = get_bigquery_client(force_mock=True)
    assert isinstance(client, MockDuckDBEngine)


def test_get_bigquery_client_mock_env_var(monkeypatch):
    """Verify get_bigquery_client returns MockDuckDBEngine when MOCK_BIGQUERY=true."""
    monkeypatch.setenv("MOCK_BIGQUERY", "true")
    client = get_bigquery_client()
    assert isinstance(client, MockDuckDBEngine)


def test_get_bigquery_client_credentials_fallback():
    """Verify get_bigquery_client gracefully falls back to MockDuckDBEngine when ADC is missing."""
    with patch(
        "src.bq.client.BigQueryClient",
        side_effect=CredentialsMissingError("Mocked ADC missing"),
    ):
        with patch.dict(os.environ, {"MOCK_BIGQUERY": "false"}, clear=False):
            client = get_bigquery_client(force_mock=False)
            assert isinstance(client, MockDuckDBEngine)
