# RFC: OPS-002A - BigQuery Live Client, Dynamic Schema Cache & Table Sanitizer

* **Related Ticket:** [OPS-002A](../../tickets/OPS-002A-bigquery-live-client.md)  
* **Parent Architecture:** [RFC-001 §3.1](RFC-001-agentic-data-assistant.md)  
* **Related ADR:** [ADR-0003](../adr/0003-bigquery-dynamic-schema-with-mock-fallback.md)  
* **Author:** AI Systems Architect & Software Engineer  
* **Status:** Approved (Peer Reviewed & Cleared)  
* **Date:** 2026-10-16  

---

## Technical Specification

This technical specification details the implementation design for the live Google Cloud BigQuery client, in-memory dynamic schema introspection cache, read-only query guardrails, and the pre-execution table qualification sanitizer (Mitigation 1).

### 1. Architectural Context & Invariants
* **Target Dataset:** `bigquery-public-data.thelook_ecommerce` (`orders`, `order_items`, `products`, `users`).
* **Table Qualification Sanitizer (Mitigation 1):** LLMs frequently generate bare SQL table names (e.g., `FROM orders` or `JOIN order_items`). Executing bare table references in BigQuery raises HTTP 404 (`Not found: Table ...`). The pre-execution sanitizer must deterministically inject full qualification (`` `bigquery-public-data.thelook_ecommerce.<table_name>` ``) before query dispatch.
* **Read-Only Safety Guardrail:** The data assistant is an analytical agent. Mutating statements (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `TRUNCATE`, `ALTER`, `CREATE`) must be intercepted and rejected before hitting BigQuery.
* **Schema Dynamic Introspection & TTL Caching:** Column definitions and data types must be fetched dynamically from `INFORMATION_SCHEMA.COLUMNS` and cached in memory with a configurable TTL (default: 3600s) to prevent network latency on repeated LLM invocations.
* **Credentials Fallback Contract:** If Google Cloud Application Default Credentials (ADC) are missing or invalid, `BigQueryClient` raises `CredentialsMissingError`, allowing the upstream client layer to trigger the offline DuckDB mock engine (OPS-002B) without crashing.

---

### 2. Module & Interface Architecture

#### 2.1 Exception Hierarchy (`src/bq/exceptions.py`)
```python
class BigQueryClientError(Exception):
    """Base exception for BigQuery client operations."""

    pass


class CredentialsMissingError(BigQueryClientError):
    """Raised when GCP ADC credentials cannot be discovered."""

    pass


class ReadOnlyQueryViolationError(BigQueryClientError):
    """Raised when a non-read-only (mutating) SQL query is attempted."""

    pass


class SchemaInspectionError(BigQueryClientError):
    """Raised when schema extraction fails."""

    pass
```

#### 2.2 Table Qualification Sanitizer (`src/bq/schema.py`)
* Signature: `sanitize_table_qualification(sql: str, dataset_id: str = "bigquery-public-data.thelook_ecommerce") -> str`
* Core Logic:
  - Scans for target table tokens: `orders`, `order_items`, `products`, `users`.
  - Recognizes keywords: `FROM`, `JOIN`, `INNER JOIN`, `LEFT JOIN`, `RIGHT JOIN`, `FULL JOIN`, `CROSS JOIN`.
  - Respects CTE declarations (`WITH <alias> AS (...)`): CTE aliases must NOT be rewritten.
  - Idempotent: If a table is already qualified (`bigquery-public-data.thelook_ecommerce.orders` or `` `bigquery-public-data.thelook_ecommerce.orders` ``), the sanitizer preserves it without double qualification.
  - Case-insensitive regex matching.

#### 2.3 Dynamic Schema Inspector & TTL Cache (`src/bq/schema.py`)
* Data Model:
  ```python
  @dataclass
  class ColumnInfo:
      column_name: str
      data_type: str
      is_nullable: bool
      description: Optional[str] = None
  ```
* Class: `SchemaInspector`
  - Attributes: `client: Optional[bigquery.Client]`, `ttl_seconds: int = 3600`, `_cache: dict[str, tuple[float, list[ColumnInfo]]]`.
  - Methods:
    - `get_table_schema(table_name: str) -> list[ColumnInfo]`: Returns column info from cache or queries `INFORMATION_SCHEMA.COLUMNS`.
    - `get_dataset_schema(tables: list[str]) -> dict[str, list[ColumnInfo]]`: Returns complete schema dictionary.
    - `format_schema_for_prompt(tables: Optional[list[str]] = None) -> str`: Formats markdown string for injection into LLM system prompt context.

#### 2.4 Live BigQuery Client (`src/bq/client.py`)
* Class: `BigQueryClient`
  - Attributes: `project_id: str`, `dataset_id: str`, `client: bigquery.Client`, `schema_inspector: SchemaInspector`.
  - Methods:
    - `__init__(project_id: Optional[str] = None, dataset_id: str = "bigquery-public-data.thelook_ecommerce")`: Initializes Google Cloud client; raises `CredentialsMissingError` if ADC is missing.
    - `is_read_only(sql: str) -> bool`: Regex verification ensuring query starts with `SELECT` or `WITH` and contains no mutating tokens (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `TRUNCATE`, `ALTER`, `CREATE`).
    - `query_to_dataframe(sql: str, sanitize: bool = True) -> pd.DataFrame`: Sanitizes table qualification, verifies read-only constraint, executes via `client.query(sql).to_dataframe()`, and returns pandas DataFrame.
    - `query_to_dicts(sql: str, sanitize: bool = True) -> list[dict[str, Any]]`: Returns query results as serializable dictionary records for LangGraph `AgentState`.

---

### 3. Step-by-Step Execution Plan

1. **Step 1:** Create `src/bq/__init__.py` and `src/bq/exceptions.py`.
2. **Step 2:** Implement `src/bq/schema.py`:
   - `ColumnInfo` dataclass.
   - `sanitize_table_qualification()` function with comprehensive regex.
   - `SchemaInspector` class with thread-safe TTL cache.
3. **Step 3:** Implement `src/bq/client.py`:
   - `is_read_only()` safety guardrail.
   - `BigQueryClient` class with credential handling, `query_to_dataframe()`, and `query_to_dicts()`.
4. **Step 4:** Implement unit tests in `tests/test_bq_schema.py`:
   - Sanitizer tests: single table, multi-table joins, already qualified, case variations, CTE preservation.
   - Read-only guard tests: allowed queries (`SELECT`, `WITH`), blocked queries (`DELETE`, `DROP`, `UPDATE`).
   - Schema cache tests: initial fetch, cached hit (no API call), TTL expiration.
   - Schema prompt formatting tests.
5. **Step 5:** Run `pytest` and `ruff check --fix .`.
6. **Step 6:** Capture execution evidence in `tests/evidence/OPS-002A/`.

---

### 4. Acceptance Criteria Checklist
- [ ] AC-1: `BigQueryClient` connects to dataset under valid GCP ADC and executes read-only GoogleSQL queries.
- [ ] AC-2: Column definitions for `orders`, `order_items`, `products`, `users` are dynamically loaded and formatted into markdown context.
- [ ] AC-3: Subsequent schema requests serve from in-memory cache without incurring network round-trips.
- [ ] AC-4: Bare table names in generated SQL are automatically rewritten with full qualification before execution.
