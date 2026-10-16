"""Unit tests for BigQuery Client, Schema Inspector, TTL Cache & Table Sanitizer."""

import time
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from google.auth.exceptions import DefaultCredentialsError

from src.bq.client import BigQueryClient, is_read_only_query
from src.bq.exceptions import (
    CredentialsMissingError,
    ReadOnlyQueryViolationError,
)
from src.bq.schema import (
    SchemaInspector,
    normalize_temporal_intervals,
    sanitize_table_qualification,
)

# ==============================================================================
# 1. Table Qualification Sanitizer Tests (Mitigation 1)
# ==============================================================================


def test_sanitize_bare_single_table():
    """Verify bare table name in FROM clause is rewritten with full dataset qualification."""
    sql = "SELECT order_id, status FROM orders WHERE status = 'Complete'"
    sanitized = sanitize_table_qualification(sql)
    assert "`bigquery-public-data.thelook_ecommerce.orders`" in sanitized
    assert "FROM `bigquery-public-data.thelook_ecommerce.orders`" in sanitized


def test_sanitize_bare_table_with_backticks():
    """Verify bare table already enclosed in backticks is rewritten without double-backticks."""
    sql = "SELECT id FROM `order_items` WHERE sale_price > 50"
    sanitized = sanitize_table_qualification(sql)
    assert "`bigquery-public-data.thelook_ecommerce.order_items`" in sanitized
    assert "``" not in sanitized


def test_sanitize_multi_table_joins():
    """Verify all bare target tables across multi-table JOINs are qualified."""
    sql = """
        SELECT o.order_id, oi.sale_price, p.brand, u.email
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        LEFT JOIN products p ON oi.product_id = p.id
        INNER JOIN users u ON o.user_id = u.id
    """
    sanitized = sanitize_table_qualification(sql)
    assert "`bigquery-public-data.thelook_ecommerce.orders`" in sanitized
    assert "`bigquery-public-data.thelook_ecommerce.order_items`" in sanitized
    assert "`bigquery-public-data.thelook_ecommerce.products`" in sanitized
    assert "`bigquery-public-data.thelook_ecommerce.users`" in sanitized


def test_sanitize_comma_separated_joins():
    """Verify ANSI-89 style comma-separated joins are properly qualified."""
    sql = "SELECT o.order_id, p.name FROM orders o, products p WHERE o.user_id = 1"
    sanitized = sanitize_table_qualification(sql)
    assert "`bigquery-public-data.thelook_ecommerce.orders`" in sanitized
    assert "`bigquery-public-data.thelook_ecommerce.products`" in sanitized


def test_sanitize_already_qualified_table_preserved():
    """Verify already qualified table references are left unchanged (idempotent)."""
    sql = "SELECT * FROM `bigquery-public-data.thelook_ecommerce.orders` WHERE status = 'Complete'"
    sanitized = sanitize_table_qualification(sql)
    assert sanitized == sql


def test_sanitize_cte_shadowing_preserved():
    """Verify that a local CTE alias shadowing a target table is NOT rewritten in the outer query."""
    sql = """
        WITH orders AS (
            SELECT 1 AS order_id, 'Complete' AS status
        )
        SELECT * FROM orders
    """
    sanitized = sanitize_table_qualification(sql)
    # The CTE alias 'orders' should not be rewritten to bigquery-public-data.thelook_ecommerce.orders
    assert "`bigquery-public-data.thelook_ecommerce.orders`" not in sanitized
    assert "SELECT * FROM orders" in sanitized


def test_normalize_temporal_intervals():
    """Verify Postgres/DuckDB style intervals are converted to GoogleSQL standard."""
    sql1 = "SELECT * FROM orders WHERE created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL '30 days')"
    assert (
        normalize_temporal_intervals(sql1)
        == "SELECT * FROM orders WHERE created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)"
    )

    sql2 = "SELECT * FROM orders WHERE created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAYS)"
    assert (
        normalize_temporal_intervals(sql2)
        == "SELECT * FROM orders WHERE created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAY)"
    )

    sql3 = "SELECT * FROM orders WHERE created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL '3' MONTH)"
    assert (
        normalize_temporal_intervals(sql3)
        == "SELECT * FROM orders WHERE created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 3 MONTH)"
    )


# ==============================================================================
# 2. Read-Only Query Guardrail Tests
# ==============================================================================


def test_is_read_only_allowed_queries():
    """Verify SELECT and WITH queries pass read-only validation."""
    assert is_read_only_query("SELECT 1")
    assert is_read_only_query("SELECT * FROM orders WHERE id = 10")
    assert is_read_only_query("WITH cte AS (SELECT 1) SELECT * FROM cte")
    # With comments
    assert is_read_only_query("-- comment\nSELECT * FROM products")
    assert is_read_only_query("/* block comment */ SELECT * FROM users")


def test_is_read_only_blocks_mutating_queries():
    """Verify mutating and destructive SQL statements are strictly rejected."""
    assert not is_read_only_query("DELETE FROM orders WHERE order_id = 1")
    assert not is_read_only_query("DROP TABLE products")
    assert not is_read_only_query("DROP VIEW order_summary")
    assert not is_read_only_query("UPDATE users SET email = 'bad@test.com'")
    assert not is_read_only_query("INSERT INTO orders (order_id) VALUES (999)")
    assert not is_read_only_query("TRUNCATE TABLE order_items")
    assert not is_read_only_query("ALTER TABLE products ADD COLUMN test STRING")
    assert not is_read_only_query("CREATE TABLE test (id INT64)")


def test_is_read_only_blocks_semicolon_chaining():
    """Verify SQL injection attempting to chain commands via semicolon is blocked."""
    assert not is_read_only_query("SELECT 1; DROP TABLE orders;")
    assert not is_read_only_query("SELECT * FROM users; DELETE FROM orders;")


# ==============================================================================
# 3. Schema Inspector & In-Memory TTL Cache Tests
# ==============================================================================


def test_schema_inspector_cache_and_ttl():
    """Verify SchemaInspector caches queries and obeys TTL expiration."""
    mock_client = MagicMock()
    mock_row1 = MagicMock(
        table_name="orders", column_name="order_id", data_type="INT64", is_nullable="NO"
    )
    mock_row2 = MagicMock(
        table_name="orders", column_name="status", data_type="STRING", is_nullable="NO"
    )
    mock_job = MagicMock()
    mock_job.result.return_value = [mock_row1, mock_row2]
    mock_client.query.return_value = mock_job

    inspector = SchemaInspector(client=mock_client, ttl_seconds=2)

    # 1. Initial call queries BigQuery
    cols = inspector.get_table_schema("orders")
    assert len(cols) == 2
    assert cols[0].column_name == "order_id"
    assert mock_client.query.call_count == 1

    # 2. Second call within TTL serves from in-memory cache without API call
    cols_cached = inspector.get_table_schema("orders")
    assert len(cols_cached) == 2
    assert mock_client.query.call_count == 1  # Still 1, no second query

    # 3. Wait for TTL to expire, next call refetches
    time.sleep(2.1)
    cols_refetched = inspector.get_table_schema("orders")
    assert len(cols_refetched) == 2
    assert mock_client.query.call_count == 2


def test_schema_inspector_static_fallback():
    """Verify SchemaInspector falls back to static schema if client is None."""
    inspector = SchemaInspector(client=None)
    schema = inspector.get_table_schema("products")
    assert len(schema) > 0
    col_names = [c.column_name for c in schema]
    assert "cost" in col_names
    assert "brand" in col_names
    assert "retail_price" in col_names


def test_format_schema_for_prompt():
    """Verify schema is formatted into clean markdown tables for prompt context."""
    inspector = SchemaInspector(client=None)
    prompt_str = inspector.format_schema_for_prompt(tables=["orders", "products"])
    assert "# BigQuery Dataset Schema" in prompt_str
    assert "### Table: `bigquery-public-data.thelook_ecommerce.orders`" in prompt_str
    assert "### Table: `bigquery-public-data.thelook_ecommerce.products`" in prompt_str
    assert "| `order_id` | `INT64` | NO |" in prompt_str


# ==============================================================================
# 4. BigQuery Client Integration & Error Handling Tests
# ==============================================================================


@patch("google.auth.default", side_effect=DefaultCredentialsError("No credentials"))
def test_bigquery_client_missing_credentials(mock_auth):
    """Verify BigQueryClient raises CredentialsMissingError on missing GCP ADC."""
    with pytest.raises(CredentialsMissingError) as exc_info:
        BigQueryClient()
    assert "Application Default Credentials (ADC) missing" in str(exc_info.value)


def test_bigquery_client_read_only_rejection():
    """Verify BigQueryClient rejects mutating query before execution."""
    mock_bqc = MagicMock()
    client = BigQueryClient(client=mock_bqc)

    with pytest.raises(ReadOnlyQueryViolationError):
        client.query_to_dataframe("DELETE FROM orders WHERE order_id = 5")

    assert mock_bqc.query.call_count == 0


def test_bigquery_client_query_to_dataframe_sanitizes():
    """Verify query_to_dataframe automatically sanitizes bare table names."""
    mock_bqc = MagicMock()
    mock_job = MagicMock()
    mock_df = pd.DataFrame([{"order_id": 100, "status": "Complete"}])
    mock_job.to_dataframe.return_value = mock_df
    mock_bqc.query.return_value = mock_job

    client = BigQueryClient(client=mock_bqc)
    result_df = client.query_to_dataframe("SELECT * FROM orders WHERE id = 100")

    assert len(result_df) == 1
    # Verify the query dispatched to BigQuery was sanitized
    called_sql = mock_bqc.query.call_args[0][0]
    assert "FROM `bigquery-public-data.thelook_ecommerce.orders`" in called_sql
