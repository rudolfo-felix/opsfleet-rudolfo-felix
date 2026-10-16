## OPS-002A: BigQuery Live Client, Dynamic Schema Cache & Table Sanitizer
Status: done  
Branch: feat/OPS-002A-bq-live-client  
Priority: High  

### Overview
Implement the production BigQuery client connecting to `bigquery-public-data.thelook_ecommerce` (`orders`, `order_items`, `products`, `users`). Implement dynamic schema inspection using `INFORMATION_SCHEMA.COLUMNS` with in-memory caching and a query pre-execution sanitizer ensuring all table references are fully qualified.

### Goal
Provide high-performance, live schema metadata to prompt generators without static hardcoding, preventing BigQuery 404 errors.

### Description
- Implement `src/bq/client.py` connecting via Google Cloud BigQuery SDK (`google.cloud.bigquery.Client`).
- Implement `src/bq/schema.py` fetching table column names, types, and descriptions dynamically from `INFORMATION_SCHEMA.COLUMNS`.
- Implement in-memory TTL caching for schema metadata.
- Implement table qualification sanitizer ensuring any bare table name (`FROM orders`) is automatically rewritten to fully qualified syntax (``FROM `bigquery-public-data.thelook_ecommerce.orders` ``) before execution (Mitigation 1).

### Acceptance Criteria
1. Given valid GCP Application Default Credentials, `BigQueryClient` connects to the dataset and executes valid read-only GoogleSQL queries.
2. Given a schema inspection request, column definitions for `orders`, `order_items`, `products`, and `users` are dynamically loaded and formatted into markdown context.
3. Subsequent schema requests serve from in-memory cache without incurring network round-trips.
4. Given generated SQL with bare table names, the pre-execution sanitizer injects full dataset qualification automatically.

### Implementation & Architecture
- 📄 **Related ADR:** [ADR-0003](../docs/adr/0003-bigquery-dynamic-schema-with-mock-fallback.md)
- 📄 **Technical Spec:** [RFC-OPS-002A](../docs/rfc/RFC-OPS-002A-bigquery-live-client.md)

### Completion Criteria
1. `src/bq/client.py` and `src/bq/schema.py` implemented.
2. Unit tests passing in `tests/test_bq_schema.py`.
