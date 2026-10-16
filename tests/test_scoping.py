"""Unit tests for row-level multi-tenant brand scoping guardrails.

Operationalizes Mitigation 2 (Conditional Brand Scoping) and verifies multi-tenant isolation.
"""

from src.guardrails.scope import (
    apply_brand_scoping,
    is_brand_scoping_required,
)


def test_unscoped_users_bypass_scoping():
    """Verify empty or wildcard allowed_brands leaves SQL unmodified."""
    sql = "SELECT * FROM `bigquery-public-data.thelook_ecommerce.products` WHERE cost > 20"

    assert apply_brand_scoping(sql, []) == sql
    assert apply_brand_scoping(sql, None) == sql
    assert apply_brand_scoping(sql, ["*"]) == sql
    assert apply_brand_scoping(sql, ["ALL"]) == sql


def test_mitigation_2_pure_user_queries_exempted():
    """AC 3: Verify queries on pure users demographics do not receive invalid brand filters."""
    users_sql = (
        "SELECT state, COUNT(*) AS user_count "
        "FROM `bigquery-public-data.thelook_ecommerce.users` "
        "WHERE country = 'United States' "
        "GROUP BY state "
        "ORDER BY user_count DESC"
    )

    # Scoping must NOT be required on pure users queries
    assert not is_brand_scoping_required(users_sql)

    # Scoping injector must return SQL completely unmodified
    scoped_sql = apply_brand_scoping(users_sql, ["Calvin Klein", "Tommy Hilfiger"])
    assert scoped_sql == users_sql
    assert "brand" not in scoped_sql.lower()


def test_mitigation_2_pure_orders_queries_exempted():
    """Verify queries on orders alone without product joins are exempted from brand injection."""
    orders_sql = (
        "SELECT status, COUNT(*) AS cnt "
        "FROM `bigquery-public-data.thelook_ecommerce.orders` "
        "WHERE created_at >= '2023-01-01' "
        "GROUP BY status"
    )
    assert not is_brand_scoping_required(orders_sql)
    scoped = apply_brand_scoping(orders_sql, ["Nike"])
    assert scoped == orders_sql


def test_brand_scoping_applied_to_products_query_without_where():
    """AC 2: Verify brand predicate is injected as WHERE clause when no WHERE exists."""
    sql = "SELECT id, name, retail_price FROM `bigquery-public-data.thelook_ecommerce.products`"
    scoped = apply_brand_scoping(sql, ["Calvin Klein"])

    assert "WHERE brand IN ('Calvin Klein')" in scoped


def test_brand_scoping_applied_with_existing_where_clause():
    """Verify brand predicate is appended with AND when WHERE clause already exists."""
    sql = (
        "SELECT id, name, retail_price "
        "FROM `bigquery-public-data.thelook_ecommerce.products` "
        "WHERE category = 'Sweaters' "
        "ORDER BY retail_price DESC"
    )
    scoped = apply_brand_scoping(sql, ["Calvin Klein", "Tommy Hilfiger"])

    assert "WHERE category = 'Sweaters' AND brand IN ('Calvin Klein', 'Tommy Hilfiger') ORDER BY" in scoped


def test_brand_scoping_with_group_by_order_by_limit():
    """Verify brand predicate inserts cleanly before GROUP BY, ORDER BY, and LIMIT boundaries."""
    sql = (
        "SELECT brand, AVG(retail_price) AS avg_price "
        "FROM `bigquery-public-data.thelook_ecommerce.products` "
        "GROUP BY brand "
        "ORDER BY avg_price DESC "
        "LIMIT 10"
    )
    scoped = apply_brand_scoping(sql, ["Levi's", "Dockers"])

    assert "WHERE brand IN ('Levi''s', 'Dockers') GROUP BY brand" in scoped


def test_brand_scoping_alias_detection():
    """Verify brand scoping resolves table aliases (e.g. p.brand IN (...))."""
    sql = (
        "SELECT p.name, oi.sale_price "
        "FROM `bigquery-public-data.thelook_ecommerce.order_items` oi "
        "JOIN `bigquery-public-data.thelook_ecommerce.products` AS p ON oi.product_id = p.id "
        "WHERE oi.status = 'Complete'"
    )
    scoped = apply_brand_scoping(sql, ["Calvin Klein"])

    assert "AND p.brand IN ('Calvin Klein')" in scoped


def test_brand_scoping_idempotency_guard():
    """Verify brand scoping does not duplicate predicate if already present."""
    sql = (
        "SELECT * FROM `bigquery-public-data.thelook_ecommerce.products` "
        "WHERE brand IN ('Calvin Klein') AND category = 'Jeans'"
    )
    scoped = apply_brand_scoping(sql, ["Calvin Klein"])

    # Must not add a second brand IN clause
    assert scoped == sql
