# ADR-0003: Dynamic BigQuery Schema Inspection with Offline Mock Fallback

* **Status:** Accepted
* **Date:** 2026-10-15
* **Deciders:** Rudolfo Félix (AI Engineer), Vlad Bondarenko (AI Tech Lead Guidance)
* **Technical Story:** [RFC-001](../rfc/RFC-001-agentic-data-assistant.md)

---

## Context & Problem Statement
The agent queries `bigquery-public-data.thelook_ecommerce` (`orders`, `order_items`, `products`, `users`). 
Hardcoding static SQL DDL strings into prompts makes the system brittle when upstream schemas evolve. Furthermore, evaluators (such as Vlad Bondarenko) running the code locally on their own machines might encounter GCP Application Default Credentials (ADC) issues, billing project setup errors, or network restrictions.

## Decision Drivers
* Dynamic schema adaptability (Requirement 1 & 5).
* Adherence to the **"2-Minute README Rule"**: Zero-friction setup for evaluators.
* Support for both live BigQuery querying and dry-run offline validation.

## Considered Options
1. **Dynamic Schema Introspection with In-Memory Caching + Offline Mock Fallback (Selected):** Inspects `INFORMATION_SCHEMA.COLUMNS` on startup, caches the structure, and provides a mock database engine if GCP credentials are unavailable or `MOCK_BIGQUERY=true`.
2. **Hardcoded Schema in Prompts:** Fast to write, but completely fails if BigQuery column types change and shows low engineering seniority.
3. **Live-Only BigQuery with No Fallback:** Strictly requires GCP ADC; causes immediate runtime failure for reviewers without an active GCP project.

## Decision Outcome
Implement `BigQueryRunner` with **Dynamic Schema Introspection** (cached in memory) and an **Automatic Mock Fallback Engine**.

### Positive Consequences
* The LLM always receives exact, up-to-date column names, types, and descriptions.
* Evaluators without active GCP billing can test 100% of the conversational UI, self-correction loop, and PII masking via `MOCK_BIGQUERY=true`.
* Prevents redundant, expensive metadata queries to BigQuery on every conversational turn.

### Negative / Neutral Consequences
* Requires maintaining a minimal mock schema definition representing `thelook_ecommerce` for offline test scenarios.
