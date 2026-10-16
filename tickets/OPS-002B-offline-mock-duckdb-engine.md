## OPS-002B: Offline Mock DuckDB Engine & Synthetic E-Commerce Fixtures
Status: backlog  
Branch: feat/OPS-002B-mock-duckdb-engine  
Priority: High  

### Overview
Implement an in-memory **DuckDB** offline mock engine providing realistic synthetic datasets for `thelook_ecommerce` (`orders`, `order_items`, `products`, `users`). Enable automatic, transparent fallback when Google Cloud Application Default Credentials (ADC) are missing or when `MOCK_BIGQUERY=true`.

### Goal
Guarantee that evaluators (Vlad Bondarenko) and automated test suites can execute 100% of the assistant's analytical, self-correction, and reporting capabilities offline with zero GCP configuration or billing prerequisites.

### Description
- Implement `src/bq/mock_engine.py` initializing an in-memory DuckDB connection (`duckdb.connect(":memory:")`).
- Seed realistic sample data conforming to `thelook_ecommerce` schema (valid dates, order statuses `'Complete'`, `'Cancelled'`, `'Returned'`, categories, costs, and retail brands).
- Wrap DuckDB execution with the same interface as `BigQueryClient` (`execute_query(sql) -> pd.DataFrame`).
- Integrate automatic fallback detection in `src/bq/client.py`: if `google.cloud.bigquery.Client()` fails due to missing credentials, gracefully route execution to `MockDuckDBEngine` with a clear Rich terminal notification.

### Acceptance Criteria
1. Given an environment without GCP credentials, running queries automatically routes to the in-memory DuckDB engine without throwing unhandled exceptions.
2. Given analytical queries on Net Revenue, Churn, or Margins, DuckDB executes the SQL query and returns non-empty pandas DataFrames.
3. DuckDB sample fixtures contain all columns required by `RFC-001` (`sale_price`, `cost`, `status`, `created_at`, `brand`, `email`, `ip_address`).

### Implementation & Architecture
- 📄 **Related ADR:** [ADR-0003](../docs/adr/0003-bigquery-dynamic-schema-with-mock-fallback.md)
- 📄 **Technical Spec:** [RFC-001](../docs/rfc/RFC-001-agentic-data-assistant.md) §3.1

### Completion Criteria
1. `src/bq/mock_engine.py` implemented with synthetic data generation.
2. Unit tests passing in `tests/test_mock_engine.py`.
