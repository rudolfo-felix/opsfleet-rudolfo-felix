# Architecture Decision Records (ADRs)

This directory contains the immutable record of key architectural choices, trade-offs, and design decisions made for the **Retail Data Analysis AI Assistant**.
We follow the **MADR (Markdown Architectural Decision Records)** standard.

---

## 📑 ADR Index

| ADR # | Title | Status | Date | Decision Summary |
|:---:|---|:---:|:---:|---|
| **[0001](./0001-adopt-langgraph-state-machine.md)** | Adopt LangGraph State Machine over Linear Chains | `Accepted` | 2026-10-15 | Use a cyclic Directed Acyclic Graph (DAG) for stateful self-correction and HITL interrupts. |
| **[0002](./0002-adopt-langfuse-oss-for-observability.md)** | Adopt Langfuse OSS over LangSmith for Enterprise Telemetry | `Accepted` | 2026-10-15 | Choose 100% MIT open-source Langfuse for zero-cost VPC self-hosting and strict GDPR/EU AI Act data sovereignty. |
| **[0003](./0003-bigquery-dynamic-schema-with-mock-fallback.md)** | Dynamic BigQuery Schema Inspection with Mock Fallback | `Accepted` | 2026-10-15 | Dynamic introspection of `thelook_ecommerce` tables paired with an offline mock engine for zero-friction evaluation. |
| **[0004](./0004-sqlite-local-storage-vs-cloudsql.md)** | Local SQLite Persistence vs. Cloud SQL for Prototype | `Accepted` | 2026-10-15 | Use zero-dependency SQLite locally for Saved Reports; specify Cloud SQL PostgreSQL in production HLD. |
| **[0005](./0005-presidio-pii-masking-vs-cloud-dlp.md)** | Deterministic Presidio PII Masking vs. Google Cloud DLP | `Accepted` | 2026-10-15 | Implement zero-latency local regex/NER sanitization to eliminate per-GB API inspection costs. |
| **[0006](./0006-configurable-gemini-flash-and-rate-limit-backoff.md)** | Configurable Gemini Flash Family & Rate-Limit Backoff | `Accepted` | 2026-10-15 | Support `gemini-2.5-flash` with exponential backoff on HTTP 429, deprecating retired 1.5 models (per Vlad Bondarenko). |
