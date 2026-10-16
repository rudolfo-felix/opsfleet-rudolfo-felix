"""Dynamic BigQuery Schema Introspection, In-Memory TTL Caching & Table Sanitizer.

Implements Invariant 6 (Table Qualification Sanitizer - Mitigation 1) and
Invariant 2 (Schema Introspection with caching).
"""

import re
import threading
import time
from dataclasses import dataclass

from google.cloud import bigquery

TARGET_TABLES = ("orders", "order_items", "products", "users")
DEFAULT_DATASET = "bigquery-public-data.thelook_ecommerce"


@dataclass
class ColumnInfo:
    """Represents column metadata from INFORMATION_SCHEMA.COLUMNS."""

    column_name: str
    data_type: str
    is_nullable: bool
    description: str | None = None


# Static schema fallback in case live INFORMATION_SCHEMA query cannot be reached
STATIC_FALLBACK_SCHEMA: dict[str, list[ColumnInfo]] = {
    "orders": [
        ColumnInfo("order_id", "INT64", False, "Primary key for the order"),
        ColumnInfo("user_id", "INT64", False, "Foreign key referencing users.id"),
        ColumnInfo(
            "status",
            "STRING",
            False,
            "Order status: Complete, Shipped, Cancelled, Returned, Processing",
        ),
        ColumnInfo("gender", "STRING", False, "Customer gender: M or F"),
        ColumnInfo("created_at", "TIMESTAMP", False, "Timestamp when the order was placed"),
        ColumnInfo("returned_at", "TIMESTAMP", True, "Timestamp when the order was returned"),
        ColumnInfo("shipped_at", "TIMESTAMP", True, "Timestamp when the order was shipped"),
        ColumnInfo("delivered_at", "TIMESTAMP", True, "Timestamp when the order was delivered"),
        ColumnInfo("num_of_item", "INT64", False, "Total quantity of items in the order"),
    ],
    "order_items": [
        ColumnInfo("id", "INT64", False, "Primary key for the order item"),
        ColumnInfo("order_id", "INT64", False, "Foreign key referencing orders.order_id"),
        ColumnInfo("user_id", "INT64", False, "Foreign key referencing users.id"),
        ColumnInfo("product_id", "INT64", False, "Foreign key referencing products.id"),
        ColumnInfo("inventory_item_id", "INT64", False, "Foreign key to inventory items"),
        ColumnInfo(
            "status", "STRING", False, "Status: Complete, Shipped, Cancelled, Returned, Processing"
        ),
        ColumnInfo("created_at", "TIMESTAMP", False, "Timestamp when order item was created"),
        ColumnInfo("shipped_at", "TIMESTAMP", True, "Timestamp when item shipped"),
        ColumnInfo("delivered_at", "TIMESTAMP", True, "Timestamp when item delivered"),
        ColumnInfo("returned_at", "TIMESTAMP", True, "Timestamp when item returned"),
        ColumnInfo("sale_price", "FLOAT64", False, "Gross item sale price in USD"),
    ],
    "products": [
        ColumnInfo("id", "INT64", False, "Primary key for the product"),
        ColumnInfo("cost", "FLOAT64", False, "Cost of goods sold (COGS) in USD"),
        ColumnInfo("category", "STRING", False, "Product category (e.g. Jeans, Sweaters, Swim)"),
        ColumnInfo("name", "STRING", False, "Product title"),
        ColumnInfo("brand", "STRING", False, "Brand name (e.g. Calvin Klein, Tommy Hilfiger)"),
        ColumnInfo("retail_price", "FLOAT64", False, "Manufacturer suggested retail price"),
        ColumnInfo("department", "STRING", False, "Department: Men or Women"),
        ColumnInfo("sku", "STRING", True, "Stock keeping unit code"),
        ColumnInfo("distribution_center_id", "INT64", False, "Fulfillment center ID"),
    ],
    "users": [
        ColumnInfo("id", "INT64", False, "Primary key for the user"),
        ColumnInfo("first_name", "STRING", False, "Customer first name (PII)"),
        ColumnInfo("last_name", "STRING", False, "Customer last name (PII)"),
        ColumnInfo("email", "STRING", False, "Customer email address (PII)"),
        ColumnInfo("age", "INT64", False, "Customer age"),
        ColumnInfo("gender", "STRING", False, "Customer gender: M or F"),
        ColumnInfo("state", "STRING", False, "US state or region"),
        ColumnInfo("street_address", "STRING", False, "Customer street address (PII)"),
        ColumnInfo("postal_code", "STRING", False, "Postal code"),
        ColumnInfo("city", "STRING", False, "City"),
        ColumnInfo("country", "STRING", False, "Country (e.g. United States)"),
        ColumnInfo("latitude", "FLOAT64", True, "Geographic latitude"),
        ColumnInfo("longitude", "FLOAT64", True, "Geographic longitude"),
        ColumnInfo("traffic_source", "STRING", False, "Acquisition channel (e.g. Search, Organic)"),
        ColumnInfo("created_at", "TIMESTAMP", False, "Account creation timestamp"),
        ColumnInfo("ip_address", "STRING", False, "Customer IPv4 address (PII)"),
    ],
}


def normalize_temporal_intervals(sql: str) -> str:
    """Normalize temporal intervals to Standard GoogleSQL format.

    Converts Postgres/DuckDB style INTERVAL '30 days' or INTERVAL '30' DAY
    to GoogleSQL syntax: INTERVAL 30 DAY.
    """
    # 1. Days: INTERVAL '30 days' or INTERVAL '30' DAY or INTERVAL 30 DAYS
    sql = re.sub(r"(?i)\bINTERVAL\s+['\"](\d+)\s+days?['\"]", r"INTERVAL \1 DAY", sql)
    sql = re.sub(r"(?i)\bINTERVAL\s+['\"]?(\d+)['\"]?\s+days?\b", r"INTERVAL \1 DAY", sql)

    # 2. Months: INTERVAL '3 months' or INTERVAL '3' MONTH or INTERVAL 3 MONTHS
    sql = re.sub(r"(?i)\bINTERVAL\s+['\"](\d+)\s+months?['\"]", r"INTERVAL \1 MONTH", sql)
    sql = re.sub(r"(?i)\bINTERVAL\s+['\"]?(\d+)['\"]?\s+months?\b", r"INTERVAL \1 MONTH", sql)

    # 3. Years: INTERVAL '1 year' or INTERVAL '1' YEAR or INTERVAL 1 YEARS
    sql = re.sub(r"(?i)\bINTERVAL\s+['\"](\d+)\s+years?['\"]", r"INTERVAL \1 YEAR", sql)
    sql = re.sub(r"(?i)\bINTERVAL\s+['\"]?(\d+)['\"]?\s+years?\b", r"INTERVAL \1 YEAR", sql)

    return sql


def extract_cte_aliases(sql: str) -> set[str]:
    """Extract Common Table Expression (CTE) aliases defined in WITH clause."""
    cte_pattern = r"(?i)\bWITH\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+AS\s*\("
    matches = set(re.findall(cte_pattern, sql))

    # Also check chained CTEs: , alias AS (
    chained_pattern = r"(?i),\s*([a-zA-Z_][a-zA-Z0-9_]*)\s+AS\s*\("
    matches.update(re.findall(chained_pattern, sql))
    return {m.lower() for m in matches}


def sanitize_table_qualification(
    sql: str,
    dataset_id: str = DEFAULT_DATASET,
    target_tables: tuple[str, ...] = TARGET_TABLES,
) -> str:
    """Pre-execution Table Qualification Sanitizer (Invariant 6 - Mitigation 1).

    Ensures that any bare table reference (e.g. `FROM orders` or `JOIN order_items`)
    is deterministically rewritten to the fully qualified BigQuery dataset reference
    `bigquery-public-data.thelook_ecommerce.<table_name>`.

    Edge cases handled:
    - Tables already fully qualified: left intact (no double qualification).
    - Tables with bare backticks: ``FROM `orders` `` -> ``FROM `dataset.orders` ``.
    - CTE aliases: if a CTE defines `WITH orders AS (...)`, references to `orders`
      outside the CTE definition are preserved as the local CTE alias.
    - Comma-separated joins: `FROM orders o, products p` -> both qualified.
    - Temporal interval normalization: `INTERVAL '30 days'` -> `INTERVAL 30 DAY`.
    """
    if not sql:
        return sql

    # Step 1: Normalize temporal intervals
    clean_sql = normalize_temporal_intervals(sql)

    # Step 2: Extract CTE aliases to avoid rewriting local CTEs
    cte_aliases = extract_cte_aliases(clean_sql)

    dataset_clean = dataset_id.strip("`")

    for table in target_tables:
        if table.lower() in cte_aliases:
            # Table name is shadowed by a local CTE alias; do not rewrite
            continue

        # Regex explanation:
        # Matches either join keyword (\b(FROM|JOIN|...)\s+) OR comma (,\s*)
        # followed by either `table` (with backticks) or bare table\b (without backticks)
        # Not followed by dot (to avoid matching column or sub-field)
        pattern = (
            rf"(?i)(?:(\b(?:FROM|JOIN|INNER\s+JOIN|LEFT\s+JOIN|RIGHT\s+JOIN|FULL\s+JOIN|CROSS\s+JOIN))\s+|,\s*)"
            rf"(?:`{re.escape(table)}`|{re.escape(table)}\b)(?!\s*\.)"
        )

        def replace_fn(match: re.Match, t: str = table) -> str:
            kw = match.group(1)
            if kw:
                return f"{kw} `{dataset_clean}.{t}`"
            return f", `{dataset_clean}.{t}`"

        clean_sql = re.sub(pattern, replace_fn, clean_sql)

    return clean_sql


class SchemaInspector:
    """Thread-safe dynamic schema inspector with in-memory TTL caching."""

    def __init__(
        self,
        client: bigquery.Client | None = None,
        dataset_id: str = DEFAULT_DATASET,
        ttl_seconds: int = 3600,
    ) -> None:
        """Initialize the SchemaInspector.

        Args:
            client: Optional Google Cloud BigQuery client instance.
            dataset_id: Fully qualified BigQuery dataset ID.
            ttl_seconds: Cache duration in seconds (default: 1 hour).
        """
        self.client = client
        self.dataset_id = dataset_id.strip("`")
        self.ttl_seconds = ttl_seconds
        self._cache: dict[str, tuple[float, list[ColumnInfo]]] = {}
        self._lock = threading.Lock()

    def get_table_schema(
        self,
        table_name: str,
        force_refresh: bool = False,
    ) -> list[ColumnInfo]:
        """Fetch schema for a specific table with TTL caching."""
        clean_table = table_name.lower().strip()
        now = time.time()

        with self._lock:
            if not force_refresh and clean_table in self._cache:
                timestamp, columns = self._cache[clean_table]
                if now - timestamp < self.ttl_seconds:
                    return columns

        # Hydrate cache via batched query or fallback
        dataset_schema = self.fetch_dataset_schema(
            tables=[clean_table],
            force_refresh=force_refresh,
        )
        return dataset_schema.get(clean_table, STATIC_FALLBACK_SCHEMA.get(clean_table, []))

    def fetch_dataset_schema(
        self,
        tables: list[str] | None = None,
        force_refresh: bool = False,
    ) -> dict[str, list[ColumnInfo]]:
        """Fetch schema metadata using a single batched INFORMATION_SCHEMA query.

        Executing a single query across all target tables hydrates the entire
        dataset cache in one network round-trip (<1.5s).
        """
        target_tables = [t.lower().strip() for t in (tables or list(TARGET_TABLES))]
        now = time.time()

        # Check if all requested tables are already cached and unexpired
        with self._lock:
            if not force_refresh:
                cached_result: dict[str, list[ColumnInfo]] = {}
                all_cached = True
                for t in target_tables:
                    if t in self._cache and (now - self._cache[t][0] < self.ttl_seconds):
                        cached_result[t] = self._cache[t][1]
                    else:
                        all_cached = False
                        break
                if all_cached:
                    return cached_result

        # Live query to INFORMATION_SCHEMA.COLUMNS if client is available
        if self.client is not None:
            table_list_str = ", ".join(f"'{t}'" for t in target_tables)
            sql = f"""
                SELECT table_name, column_name, data_type, is_nullable
                FROM `{self.dataset_id}.INFORMATION_SCHEMA.COLUMNS`
                WHERE table_name IN ({table_list_str})
                ORDER BY table_name, ordinal_position;
            """
            try:
                query_job = self.client.query(sql)
                rows = list(query_job.result())

                new_schema: dict[str, list[ColumnInfo]] = {t: [] for t in target_tables}
                for row in rows:
                    t_name = str(row.table_name).lower()
                    if t_name in new_schema:
                        new_schema[t_name].append(
                            ColumnInfo(
                                column_name=str(row.column_name),
                                data_type=str(row.data_type),
                                is_nullable=(str(row.is_nullable).upper() == "YES"),
                            )
                        )

                with self._lock:
                    for t_name, cols in new_schema.items():
                        if cols:
                            self._cache[t_name] = (now, cols)

                return {
                    t: self._cache.get(t, (now, STATIC_FALLBACK_SCHEMA.get(t, [])))[1]
                    for t in target_tables
                }
            except Exception:
                # If network or credentials fail, log and fall back to static schema
                pass

        # Static fallback if client is absent or network fails
        with self._lock:
            for t in target_tables:
                if t in STATIC_FALLBACK_SCHEMA:
                    self._cache[t] = (now, STATIC_FALLBACK_SCHEMA[t])
            return {t: self._cache.get(t, (now, []))[1] for t in target_tables}

    def format_schema_for_prompt(self, tables: list[str] | None = None) -> str:
        """Format dynamic table schemas into clean markdown context for LLM prompts."""
        target_tables = tables or list(TARGET_TABLES)
        schema_dict = self.fetch_dataset_schema(tables=target_tables)

        sections: list[str] = [
            f"# BigQuery Dataset Schema: `{self.dataset_id}`\n",
            "Use the following table and column definitions to construct accurate GoogleSQL queries:\n",
        ]

        for table in target_tables:
            columns = schema_dict.get(table, STATIC_FALLBACK_SCHEMA.get(table, []))
            sections.append(f"### Table: `{self.dataset_id}.{table}`")
            sections.append("| Column Name | Data Type | Nullable | Description |")
            sections.append("|---|---|:---:|---|")
            for col in columns:
                desc = col.description or ""
                nullable = "YES" if col.is_nullable else "NO"
                sections.append(
                    f"| `{col.column_name}` | `{col.data_type}` | {nullable} | {desc} |"
                )
            sections.append("")

        return "\n".join(sections)
