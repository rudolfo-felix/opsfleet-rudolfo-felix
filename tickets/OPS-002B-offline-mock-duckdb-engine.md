## OPS-002B: Offline Mock DuckDB Engine & Synthetic E-Commerce Fixtures
Status: done  
Branch: feat/OPS-002B-mock-duckdb-engine  
Priority: High  

### Overview
Implement an in-memory **DuckDB** offline mock engine providing realistic synthetic datasets for `thelook_ecommerce` (`orders`, `order_items`, `products`, `users`). Enable automatic, transparent fallback when Google Cloud Application Default Credentials (ADC) are missing or when `MOCK_BIGQUERY=true`.

### Goal
Guarantee that evaluators (Vlad Bondarenko) and automated test suites can execute 100% of the assistant's analytical, self-correction, and reporting capabilities offline with zero GCP configuration or billing prerequisites.

### Description
- Implement `src/bq/mock_engine.py` initializing an in-memory DuckDB connection (`duckdb.connect(":memory:")`).
- Seed realistic sample data conforming to `thelook_ecommerce` schema: $\ge 50$ rows per table, orders spanning $\ge 6$ calendar months, $\ge 3$ distinct US states, valid order statuses (`'Complete'`, `'Cancelled'`, `'Returned'`), retail categories, costs, and brands.
- Implement a SQL dialect normalizer in `mock_engine.py` that translates BigQuery GoogleSQL nuances to DuckDB before execution:
  - Strips backtick-qualified table names: `` `bigquery-public-data.thelook_ecommerce.<table>` `` or `` `thelook_ecommerce.<table>` `` $\rightarrow$ `<table>`.
  - Normalizes temporal intervals: `TIMESTAMP_SUB(..., INTERVAL X DAY)` $\rightarrow$ `... - INTERVAL 'X' DAY`.
  - Normalizes date truncation: `DATE_TRUNC(col, MONTH)` $\rightarrow$ `DATE_TRUNC('month', col)`.
  - Normalizes safe division: `SAFE_DIVIDE(a, b)` $\rightarrow$ `CASE WHEN b = 0 THEN NULL ELSE (a * 1.0) / b END`.
  - Normalizes double-quoted string literals in WHERE clauses to standard SQL single quotes.
- Wrap DuckDB execution with the same interface as `BigQueryClient` (`execute_query(sql) -> pd.DataFrame`).
- Integrate automatic fallback detection in `src/bq/client.py`: if `google.cloud.bigquery.Client()` fails due to missing credentials, gracefully route execution to `MockDuckDBEngine` with a clear Rich terminal notification.

### Acceptance Criteria
1. Given an environment without GCP credentials, running queries automatically routes to the in-memory DuckDB engine without throwing unhandled exceptions.
2. Given analytical queries on Net Revenue, Churn, or Margins, DuckDB executes the SQL query and returns non-empty pandas DataFrames.
3. DuckDB sample fixtures contain all columns required by `RFC-001` (`sale_price`, `cost`, `status`, `created_at`, `brand`, `email`, `ip_address`) with $\ge 50$ rows spanning $\ge 6$ months.
4. Given GoogleSQL-specific constructs (backtick table qualifications, `TIMESTAMP_SUB`, `SAFE_DIVIDE`), the dialect normalizer converts them transparently so DuckDB executes without syntax errors.

### Implementation & Architecture
- 📄 **Related ADR:** [ADR-0003](../docs/adr/0003-bigquery-dynamic-schema-with-mock-fallback.md)
- 📄 **Technical Spec:** [RFC-001](../docs/rfc/RFC-001-agentic-data-assistant.md) §3.1

### Completion Criteria
1. `src/bq/mock_engine.py` implemented with synthetic data generation and GoogleSQL-to-DuckDB normalization.
2. Unit tests passing in `tests/test_mock_engine.py`.
