"""Enterprise Row-Level Multi-Tenant Brand Scoping Guardrail.

Operationalizes Mitigation 2 (Conditional Brand Scoping) and prevents cross-tenant data leakage
between category directors (e.g. Marcus persona restricted to specific brands).
"""

import re
from collections.abc import Sequence

# SQL keywords marking the boundary of WHERE clause
CLAUSE_BOUNDARIES = [
    r"\bGROUP\s+BY\b",
    r"\bORDER\s+BY\b",
    r"\bHAVING\b",
    r"\bLIMIT\b",
    r"\bQUALIFY\b",
    r"\bWINDOW\b",
]

BOUNDARY_PATTERN = re.compile(
    r"(" + "|".join(CLAUSE_BOUNDARIES) + r")",
    re.IGNORECASE,
)


def is_brand_scoping_required(sql: str) -> bool:
    """Determine whether a query requires brand scoping (Mitigation 2).

    Exemption Rule: Pure user demographic or customer analytics queries that ONLY reference
    the `users` table without joining `products` or `order_items` must NOT have a brand
    predicate injected, avoiding BigQuery error 400 'Unrecognized name: brand'.
    """
    if not sql:
        return False

    sql_lower = sql.lower()

    # If the query directly mentions brand column or table products/order_items
    has_products = bool(re.search(r"\bproducts\b", sql_lower))
    has_order_items = bool(re.search(r"\border_items\b", sql_lower))
    has_brand = bool(re.search(r"\bbrand\b", sql_lower))

    if has_products or has_brand:
        return True

    # If only order_items is present without products, brand isn't directly on order_items,
    # but if order_items is queried, brand scoping can only be applied if products is joined
    if has_order_items:
        return False

    return False


def _detect_products_alias(sql: str) -> str | None:
    """Detect table alias assigned to products table if present."""
    # Matches patterns like: `...products` AS p, products p, `thelook_ecommerce.products` p
    pattern = re.compile(
        r"(?:`?[a-zA-Z0-9_.-]*products`?)\s+(?:AS\s+)?([a-zA-Z0-9_]+)",
        re.IGNORECASE,
    )
    for match in pattern.finditer(sql):
        candidate = match.group(1).strip()
        # Ensure candidate is not a SQL keyword
        if candidate.upper() not in {
            "ON", "JOIN", "WHERE", "GROUP", "ORDER", "HAVING", "LIMIT",
            "LEFT", "RIGHT", "INNER", "OUTER", "CROSS", "FULL", "USING"
        }:
            return candidate
    return None


def apply_brand_scoping(sql: str, allowed_brands: Sequence[str] | None) -> str:
    """Inject brand scoping predicates into SQL query for multi-tenant isolation.

    Enforces:
    1. Unscoped pass-through when allowed_brands is empty or contains '*'
    2. Exemption when query does not touch products/brand (Mitigation 2)
    3. Idempotent non-duplication if brand filter already present
    4. Table alias resolution (e.g. p.brand IN (...) vs brand IN (...))
    """
    if not sql or not sql.strip():
        return sql

    if not allowed_brands:
        return sql

    # Unscoped administrative permissions
    if any(b.strip() in ("*", "all", "ALL") for b in allowed_brands):
        return sql

    # Mitigation 2: Exclude queries that don't target products or brand
    if not is_brand_scoping_required(sql):
        return sql

    # Idempotency check: avoid double-injecting if brand predicate already exists
    if re.search(r"\b(?:[a-zA-Z0-9_]+\.)?brand\s+IN\b", sql, re.IGNORECASE):
        return sql

    # Format brand literals safely
    escaped_brands = [f"'{b.replace(chr(39), chr(39) * 2)}'" for b in allowed_brands if b.strip()]
    if not escaped_brands:
        return sql

    brand_in_list = ", ".join(escaped_brands)

    # Resolve alias if present
    alias = _detect_products_alias(sql)
    column_ref = f"{alias}.brand" if alias else "brand"
    predicate = f"{column_ref} IN ({brand_in_list})"

    sql_stripped = sql.strip().rstrip(";")

    # Check if a WHERE clause is present
    where_match = re.search(r"\bWHERE\b", sql_stripped, re.IGNORECASE)

    if where_match:
        # WHERE clause exists. Find if there's a subsequent boundary (GROUP BY, ORDER BY, LIMIT, etc.)
        where_pos = where_match.start()
        post_where = sql_stripped[where_pos:]
        boundary_match = BOUNDARY_PATTERN.search(post_where)

        if boundary_match:
            insert_idx = where_pos + boundary_match.start()
            scoped_sql = (
                sql_stripped[:insert_idx].rstrip()
                + f" AND {predicate} "
                + sql_stripped[insert_idx:].lstrip()
            )
        else:
            scoped_sql = f"{sql_stripped} AND {predicate}"
    else:
        # No WHERE clause exists. Find earliest boundary clause (GROUP BY, ORDER BY, LIMIT, etc.)
        boundary_match = BOUNDARY_PATTERN.search(sql_stripped)
        if boundary_match:
            insert_idx = boundary_match.start()
            scoped_sql = (
                sql_stripped[:insert_idx].rstrip()
                + f" WHERE {predicate} "
                + sql_stripped[insert_idx:].lstrip()
            )
        else:
            scoped_sql = f"{sql_stripped} WHERE {predicate}"

    return scoped_sql
