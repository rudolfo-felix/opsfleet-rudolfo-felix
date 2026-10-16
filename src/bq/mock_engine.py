"""In-memory DuckDB Mock Engine with synthetic thelook_ecommerce datasets.

Operationalizes Invariant 1 (2-Minute Evaluator Rule) and Invariant 5 (Dual BigQuery Strategy)
by providing zero-dependency offline execution for evaluators without GCP credentials.
"""

import datetime
import logging
import random
import re
from typing import Any

import duckdb
import pandas as pd
from rich.console import Console

from src.bq.client import is_read_only_query
from src.bq.exceptions import BigQueryClientError, ReadOnlyQueryViolationError
from src.bq.schema import DEFAULT_DATASET, SchemaInspector

logger = logging.getLogger(__name__)
console = Console()


def _replace_safe_divide(sql: str) -> str:
    """Robustly replace SAFE_DIVIDE(a, b) with (CAST(a AS DOUBLE) / NULLIF(b, 0)).

    Handles arbitrary nested parentheses in arguments (e.g. SUM(...), COUNT(DISTINCT ...)).
    """
    pattern = re.compile(r"(?i)\bSAFE_DIVIDE\s*\(")
    while True:
        match = pattern.search(sql)
        if not match:
            break

        start_idx = match.start()
        args_start = match.end()

        # Parse arguments until matching closing parenthesis
        depth = 1
        comma_idx = -1
        idx = args_start
        in_single_quote = False

        while idx < len(sql) and depth > 0:
            char = sql[idx]
            if char == "'":
                in_single_quote = not in_single_quote
            elif not in_single_quote:
                if char == "(":
                    depth += 1
                elif char == ")":
                    depth -= 1
                    if depth == 0:
                        break
                elif char == "," and depth == 1:
                    comma_idx = idx
            idx += 1

        if depth != 0 or comma_idx == -1:
            # Malformed SAFE_DIVIDE call; avoid infinite loop
            break

        arg1 = sql[args_start:comma_idx].strip()
        arg2 = sql[comma_idx + 1 : idx].strip()
        end_idx = idx + 1

        replacement = f"(CAST(({arg1}) AS DOUBLE) / NULLIF(({arg2}), 0))"
        sql = sql[:start_idx] + replacement + sql[end_idx:]

    return sql


def translate_googlesql_to_duckdb(sql: str) -> str:
    """Translate BigQuery GoogleSQL queries into valid DuckDB SQL syntax.

    Nuances handled:
    1. Table qualifications: strips `bigquery-public-data.thelook_ecommerce.<table>`
       or `thelook_ecommerce.<table>` to bare `<table>`.
    2. Strips backticks from table and column identifiers.
    3. Translates TIMESTAMP_SUB / DATE_SUB(expr, INTERVAL N UNIT) -> (expr - INTERVAL 'N' UNIT).
    4. Translates TIMESTAMP_ADD / DATE_ADD(expr, INTERVAL N UNIT) -> (expr + INTERVAL 'N' UNIT).
    5. Translates DATE_TRUNC / TIMESTAMP_TRUNC(expr, PART) -> date_trunc('part', expr) (argument inversion).
    6. Translates SAFE_DIVIDE(a, b) -> (CAST((a) AS DOUBLE) / NULLIF((b), 0)).
    7. Translates COUNTIF(expr) -> COUNT_IF(expr).
    8. Translates CURRENT_DATETIME() -> CURRENT_TIMESTAMP.
    9. Converts double-quoted string literals in filter expressions to single quotes.
    """
    if not sql:
        return sql

    translated = sql

    # 1. Strip dataset qualifications: `bigquery-public-data.thelook_ecommerce.table` -> `table`
    translated = re.sub(
        r"(?i)`?(?:bigquery-public-data\.)?thelook_ecommerce\.([a-zA-Z0-9_]+)`?",
        r"\1",
        translated,
    )

    # 2. Strip remaining backticks around identifiers
    translated = re.sub(r"`([a-zA-Z0-9_]+)`", r"\1", translated)

    # 3. Temporal subtraction: TIMESTAMP_SUB / DATE_SUB(expr, INTERVAL X UNIT)
    sub_pattern = r"(?i)\b(?:TIMESTAMP|DATE)_SUB\s*\(\s*(.*?)\s*,\s*INTERVAL\s+['\"]?(\d+)['\"]?\s+([a-zA-Z]+)\s*\)"
    translated = re.sub(sub_pattern, r"(\1 - INTERVAL '\2' \3)", translated)

    # 4. Temporal addition: TIMESTAMP_ADD / DATE_ADD(expr, INTERVAL X UNIT)
    add_pattern = r"(?i)\b(?:TIMESTAMP|DATE)_ADD\s*\(\s*(.*?)\s*,\s*INTERVAL\s+['\"]?(\d+)['\"]?\s+([a-zA-Z]+)\s*\)"
    translated = re.sub(add_pattern, r"(\1 + INTERVAL '\2' \3)", translated)

    # 5. Date / Timestamp Truncation with argument inversion:
    # BigQuery: DATE_TRUNC(expr, MONTH) -> DuckDB: date_trunc('month', expr)
    def repl_trunc(m: re.Match) -> str:
        expr = m.group(1).strip()
        part = m.group(2).strip().lower()
        return f"date_trunc('{part}', {expr})"

    trunc_pattern = r"(?i)\b(?:DATE|TIMESTAMP)_TRUNC\s*\(\s*(.*?)\s*,\s*([a-zA-Z]+)\s*\)"
    translated = re.sub(trunc_pattern, repl_trunc, translated)

    # 6. SAFE_DIVIDE replacement via balanced parser
    translated = _replace_safe_divide(translated)

    # 7. COUNTIF -> COUNT_IF
    translated = re.sub(r"(?i)\bCOUNTIF\(", "COUNT_IF(", translated)

    # 8. CURRENT_DATETIME() / CURRENT_TIMESTAMP() -> CURRENT_TIMESTAMP
    translated = re.sub(r"(?i)\bCURRENT_(?:DATETIME|TIMESTAMP)\(\)", "CURRENT_TIMESTAMP", translated)

    # 9. Double-quoted string literals in expressions: e.g. status = "Complete" -> status = 'Complete'
    # Match double quotes following comparison operators or IN (
    translated = re.sub(
        r'(?i)(=\s*|!=\s*|<>\s*|\bIN\s*\(\s*)"([^"]+)"',
        r"\1'\2'",
        translated,
    )
    # Also handle subsequent items in IN list: , "Cancelled" -> , 'Cancelled'
    translated = re.sub(
        r',\s*"([^"]+)"',
        r", '\1'",
        translated,
    )

    # 10. TIMESTAMP('...') -> TIMESTAMP '...'
    translated = re.sub(r"(?i)\bTIMESTAMP\s*\(\s*('[^']+')\s*\)", r"TIMESTAMP \1", translated)

    return translated


def generate_synthetic_data() -> dict[str, pd.DataFrame]:
    """Generate realistic, referentially consistent e-commerce fixtures for thelook_ecommerce.

    Yields:
    - users: >= 60 rows with PII (email, first_name, last_name, ip_address), 6 US states.
    - products: >= 50 rows across 7 brands and 6 categories with realistic COGS and retail prices.
    - orders: >= 75 rows spanning 15 calendar months (2025-01 to 2026-03) with realistic statuses.
    - order_items: >= 100 rows linked to users, orders, and products.
    """
    rng = random.Random(42)

    # 1. Users fixture (65 rows)
    first_names = [
        "Emma",
        "Liam",
        "Olivia",
        "Noah",
        "Sophia",
        "Jackson",
        "Ava",
        "Aiden",
        "Isabella",
        "Lucas",
        "Mia",
        "Oliver",
        "Harper",
        "Ethan",
        "Evelyn",
        "Elijah",
        "Abigail",
        "James",
        "Emily",
        "Benjamin",
    ]
    last_names = [
        "Smith",
        "Johnson",
        "Williams",
        "Brown",
        "Jones",
        "Garcia",
        "Miller",
        "Davis",
        "Rodriguez",
        "Martinez",
        "Hernandez",
        "Lopez",
        "Gonzalez",
        "Wilson",
        "Anderson",
        "Thomas",
        "Taylor",
        "Moore",
        "Jackson",
        "Martin",
    ]
    states = ["CA", "NY", "TX", "FL", "IL", "WA"]
    cities = {
        "CA": "San Francisco",
        "NY": "New York",
        "TX": "Austin",
        "FL": "Miami",
        "IL": "Chicago",
        "WA": "Seattle",
    }
    traffic_sources = ["Search", "Organic", "Facebook", "Email"]

    user_rows = []
    base_user_date = datetime.datetime(2024, 1, 15, 10, 0, 0)
    for uid in range(1, 66):
        fn = rng.choice(first_names)
        ln = rng.choice(last_names)
        st = rng.choice(states)
        created_at = base_user_date + datetime.timedelta(days=uid * 5, hours=rng.randint(0, 23))
        user_rows.append(
            {
                "id": uid,
                "first_name": fn,
                "last_name": ln,
                "email": f"{fn.lower()}.{ln.lower()}{uid}@example.com",
                "age": rng.randint(21, 68),
                "gender": rng.choice(["M", "F"]),
                "state": st,
                "street_address": f"{100 + uid} Market Street",
                "postal_code": f"{90000 + uid}",
                "city": cities[st],
                "country": "United States",
                "latitude": round(37.77 + (uid * 0.01), 4),
                "longitude": round(-122.41 - (uid * 0.01), 4),
                "traffic_source": rng.choice(traffic_sources),
                "created_at": created_at,
                "ip_address": f"192.168.1.{uid}",
            }
        )
    df_users = pd.DataFrame(user_rows)

    # 2. Products fixture (50 rows)
    brands = ["Calvin Klein", "Tommy Hilfiger", "Nike", "Levi's", "Adidas", "Puma", "Under Armour"]
    categories = ["Jeans", "Sweaters", "Swim", "Tops & Tees", "Accessories", "Outerwear"]
    departments = ["Men", "Women"]

    product_rows = []
    for pid in range(1, 51):
        brand = brands[(pid - 1) % len(brands)]
        cat = categories[(pid - 1) % len(categories)]
        dept = departments[(pid - 1) % len(departments)]
        cost = round(15.0 + (pid * 2.1), 2)
        # Retail price marked up by 1.6x - 2.2x
        markup = 1.6 + ((pid % 5) * 0.12)
        retail_price = round(cost * markup, 2)
        product_rows.append(
            {
                "id": pid,
                "cost": cost,
                "category": cat,
                "name": f"{brand} {cat} #{pid}",
                "brand": brand,
                "retail_price": retail_price,
                "department": dept,
                "sku": f"SKU-{2000 + pid}",
                "distribution_center_id": (pid % 5) + 1,
            }
        )
    df_products = pd.DataFrame(product_rows)

    # 3. Orders fixture (80 rows spanning Jan 2025 - Mar 2026, 15 months)
    # Realistic status proportions: 60% Complete, 15% Shipped, 10% Returned, 10% Cancelled, 5% Processing
    statuses = (
        ["Complete"] * 48
        + ["Shipped"] * 12
        + ["Returned"] * 8
        + ["Cancelled"] * 8
        + ["Processing"] * 4
    )
    rng.shuffle(statuses)

    order_rows = []
    start_order_date = datetime.datetime(2025, 1, 5, 9, 30, 0)
    for oid in range(1, 81):
        uid = (oid % 65) + 1
        status = statuses[oid - 1]
        created_at = start_order_date + datetime.timedelta(days=(oid - 1) * 5 + rng.randint(0, 3))

        shipped_at = (
            created_at + datetime.timedelta(days=2)
            if status in ("Complete", "Shipped", "Returned")
            else None
        )
        delivered_at = (
            shipped_at + datetime.timedelta(days=3) if status in ("Complete", "Returned") else None
        )
        returned_at = delivered_at + datetime.timedelta(days=5) if status == "Returned" else None

        user_gender = df_users.loc[df_users["id"] == uid, "gender"].values[0]
        num_items = rng.randint(1, 3)

        order_rows.append(
            {
                "order_id": oid,
                "user_id": uid,
                "status": status,
                "gender": user_gender,
                "created_at": created_at,
                "returned_at": returned_at,
                "shipped_at": shipped_at,
                "delivered_at": delivered_at,
                "num_of_item": num_items,
            }
        )
    df_orders = pd.DataFrame(order_rows)

    # 4. Order Items fixture (110 rows)
    order_item_rows = []
    item_id = 1
    for _, o in df_orders.iterrows():
        oid = int(o["order_id"])
        uid = int(o["user_id"])
        ostatus = o["status"]
        ocreated_at = o["created_at"]
        oshipped_at = o["shipped_at"]
        odelivered_at = o["delivered_at"]
        oreturned_at = o["returned_at"]

        num_items = int(o["num_of_item"])
        for _ in range(num_items):
            pid = rng.randint(1, 50)
            base_price = df_products.loc[df_products["id"] == pid, "retail_price"].values[0]
            # Occasional small promotion discount
            discount = rng.choice([0.0, 0.05, 0.10])
            sale_price = round(base_price * (1.0 - discount), 2)

            order_item_rows.append(
                {
                    "id": item_id,
                    "order_id": oid,
                    "user_id": uid,
                    "product_id": pid,
                    "inventory_item_id": 1000 + item_id,
                    "status": ostatus,
                    "created_at": ocreated_at,
                    "shipped_at": oshipped_at,
                    "delivered_at": odelivered_at,
                    "returned_at": oreturned_at,
                    "sale_price": sale_price,
                }
            )
            item_id += 1
            if item_id > 110:
                break
        if item_id > 110:
            break

    df_order_items = pd.DataFrame(order_item_rows)

    return {
        "users": df_users,
        "products": df_products,
        "orders": df_orders,
        "order_items": df_order_items,
    }


class MockDuckDBEngine:
    """In-memory DuckDB query engine providing full offline parity with BigQueryClient."""

    def __init__(self, dataset_id: str = DEFAULT_DATASET) -> None:
        """Initialize in-memory DuckDB catalog and seed synthetic datasets."""
        self.dataset_id = dataset_id.strip("`")
        self.con = duckdb.connect(":memory:")
        self.schema_inspector = SchemaInspector(client=None, dataset_id=self.dataset_id)
        self._seed_fixtures()

    def _seed_fixtures(self) -> None:
        """Register synthetic datasets into the in-memory DuckDB catalog."""
        fixtures = generate_synthetic_data()
        for table_name, df in fixtures.items():
            self.con.register(f"temp_{table_name}_df", df)
            self.con.execute(f"CREATE TABLE {table_name} AS SELECT * FROM temp_{table_name}_df")
            self.con.unregister(f"temp_{table_name}_df")
            logger.debug(f"Seeded DuckDB table '{table_name}' with {len(df)} rows.")

    def execute_query(self, sql: str, sanitize: bool = True) -> duckdb.DuckDBPyRelation:
        """Execute translated query against in-memory DuckDB."""
        if not is_read_only_query(sql):
            raise ReadOnlyQueryViolationError(
                f"Query rejected: Only read-only SELECT and WITH statements are permitted. Query: {sql[:100]}"
            )

        translated = translate_googlesql_to_duckdb(sql)
        logger.debug(f"Executing DuckDB SQL: {translated}")
        try:
            return self.con.sql(translated)
        except Exception as e:
            raise BigQueryClientError(f"DuckDB execution failed: {e}") from e

    def query_to_dataframe(self, sql: str, sanitize: bool = True) -> pd.DataFrame:
        """Execute read-only SQL and return results as a Pandas DataFrame."""
        rel = self.execute_query(sql, sanitize=sanitize)
        try:
            return rel.df()
        except Exception as e:
            raise BigQueryClientError(f"DuckDB query to dataframe failed: {e}") from e

    def query_to_dicts(self, sql: str, sanitize: bool = True) -> list[dict[str, Any]]:
        """Execute read-only SQL and return serializable records."""
        df = self.query_to_dataframe(sql, sanitize=sanitize)
        records = df.to_dict(orient="records")
        for record in records:
            for k, v in record.items():
                if pd.isna(v):
                    record[k] = None
                elif hasattr(v, "isoformat"):
                    record[k] = v.isoformat()
        return records
