## OPS-002: BigQuery Client, Dynamic Schema Caching & Mock Engine
Status: backlog  
Branch: feat/OPS-002-bigquery-client  
Priority: High  

### Overview
Build the Google Cloud BigQuery client interface to query `bigquery-public-data.thelook_ecommerce`, extract real table metadata dynamically (`orders`, `order_items`, `products`, `users`), cache schemas in memory, and provide an offline mock engine for zero-friction evaluation.

### Goal
Allow the agent to dynamically inspect database structure and execute read-only GoogleSQL safely, with full offline simulation support if GCP credentials are absent.

### Acceptance Criteria
1. Given an active GCP project, when querying `thelook_ecommerce`, tables `orders`, `order_items`, `products`, `users` return correct column definitions and types.
2. Given `MOCK_BIGQUERY=true` or absent GCP ADC, when executing a query, the mock engine intercepts the call and returns realistic sample DataFrames without raising authentication crashes.
3. Given schema metadata, it is cached in-memory after initial load to avoid repetitive BigQuery metadata API billing.

### Implementation & Architecture
* 📄 **Related ADR:** [ADR-0003](../docs/adr/0003-bigquery-dynamic-schema-with-mock-fallback.md)
* 📄 **Technical Spec:** [RFC-001](../docs/rfc/RFC-001-agentic-data-assistant.md)

### Completion Criteria
1. `src/bq/client.py` and `src/bq/schema.py` implemented.
2. Verified with unit test asserting schema formatting and mock query execution.
