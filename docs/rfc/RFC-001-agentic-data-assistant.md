# RFC-001: Architecture & Engineering Design for Retail Data Analysis Agent

* **RFC ID:** RFC-001
* **Related PRD:** [PRD-RETAIL-ASSISTANT.md](../prd/PRD-RETAIL-ASSISTANT.md)
* **Author:** Rudolfo Félix (AI Engineer Candidate)
* **Status:** Accepted
* **Created Date:** 2026-10-15
* **Target Version:** v1.0.0

---

## 1. Abstract & Context

This document outlines the complete technical design for the **Retail Data Analysis AI Assistant**. The solution leverages a stateful **LangGraph StateGraph** coupled with Google Gemini (`gemini-2.5-flash` / configurable Flash family) to translate natural language questions from retail executives into SQL, execute them safely against Google Cloud BigQuery (`thelook_ecommerce`), enforce PII redaction and brand scoping, manage saved reports via human-in-the-loop oversight, and provide self-healing query retries.

---

## 2. Architecture & Data Flow

### 2.1 StateGraph Architecture
The agent is modeled as a state machine governed by typed state transitions:

```text
[User Query] 
     │
     ▼
[intent_router] ──(Destructive: "Delete reports...")──> [hitl_interrupt_node] ──> [storage_purge] ──> [END]
     │
     └──(Analytical Query)──> [sql_generator] 
                                    │
                                    ▼
                             [bq_executor]
                               │       │
                     (Valid DataFrame) (SQL Error / Empty Return)
                               │       │
                               │       ▼
                               │   [self_correct] ──(Max 2 retries)──> [bq_executor]
                               ▼
                        [pii_sanitizer]
                               │
                               ▼
                       [report_synthesizer]
                               │
                               ▼
                             [END]
```

### 2.2 Shared Agent State (`AgentState`)
```python
from typing import TypedDict, List, Dict, Any, Optional

class AgentState(TypedDict):
    user_query: str
    user_id: str
    allowed_brands: List[str]
    current_sql: Optional[str]
    sql_history: List[str]
    error_feedback: Optional[str]
    retry_count: int
    query_results: Optional[List[Dict[str, Any]]]
    sanitized_results: Optional[List[Dict[str, Any]]]
    executive_report: Optional[str]
    requires_confirmation: bool
    confirmation_status: Optional[bool]
    token_usage: Dict[str, int]
```

---

## 3. Detailed Component Specifications

### 3.1 BigQuery Client & Schema Engine (`src/bq/`)
* **Live Integration:** Connects to `bigquery-public-data.thelook_ecommerce` using Google Cloud BigQuery Python SDK (`google-cloud-bigquery`).
* **Schema Introspection:** Dynamically extracts schema definitions (`orders`, `order_items`, `products`, `users`) with in-memory caching to avoid round-trip latency.
* **Mock / Offline Fallback:** Includes a built-in mock engine with sample schemas and generated rows. If GCP credentials or billing are absent, the evaluator can still experience 100% of the conversational and self-correction flows.

### 3.2 SQL Generator & Scoping Guard (`src/agent/` & `src/guardrails/`)
* **Dialect:** Standard GoogleSQL (BigQuery).
* **Few-shot Prompting:** Guided by exemplar Trios mimicking the Golden Bucket.
* **Deterministic Scope Injection:** Before execution, user constraints (`allowed_brands`) are verified in the generated SQL `WHERE` clause or injected deterministically to prevent multi-tenant data leakage.

### 3.3 Self-Correction & Reflection Loop (`src/agent/`)
* **Trigger:** Traps BigQuery client errors (e.g., `400 Column not found`, invalid type casts) or queries returning zero rows.
* **Feedback Mechanism:** The compiler error message is reinjected into the prompt context.
* **Circuit Breaker:** Capped strictly at `retry_count <= 2` to preserve Google AI Studio free tier quotas and adhere to FinOps budgets.

### 3.4 PII Sanitizer Gate (`src/guardrails/pii.py`)
* **Rules:** Deterministic regex patterns + NLP masking.
* **Targets:** Email addresses (`[EMAIL_REDACTED]`), IPv4/IPv6 (`[IP_REDACTED]`), customer names from the `users` table.
* **Defense-in-Depth:** Runs on both raw SQL query dataframes and the synthesized final markdown.

### 3.5 Saved Reports & High-Stakes Oversight (`src/storage/`)
* **Store:** Lightweight local SQLite database (`reports.db`).
* **Interrupt Flow:** Deletion commands trigger an explicit prompt (`Are you sure you want to delete report #X? [y/N]`). Deletion only executes if the user confirms with `y` or `yes`.

### 3.6 Observability & Telemetry (`src/telemetry/`)
* Emits structured OpenTelemetry-aligned logs conforming to `gen_ai.*` semantic conventions.
* Tracks: latency per node, prompt/completion token consumption, self-correction attempt counts, and PII masking triggers.
* Isolates sensitive user queries and raw database rows from standard span attributes to prevent telemetry data leaks.

---

## 4. Error Handling & Rate Limit Resilience

* **HTTP 429 (`RESOURCE_EXHAUSTED`):** Implements exponential backoff with jitter (initial delay 2s, factor 2, max 3 retries).
* **CLI Feedback:** Uses `rich.console` to display informative warning status boxes without terminating the active session.

---

## 5. Alternatives Considered & Architectural Decisions

* *Why LangGraph over linear LangChain chains?* Evaluated in [ADR-0001](../adr/0001-adopt-langgraph-state-machine.md).
* *Why Langfuse OSS over LangSmith?* Evaluated in [ADR-0002](../adr/0002-adopt-langfuse-oss-for-observability.md).
* *Why BigQuery schema cache + mock fallback?* Evaluated in [ADR-0003](../adr/0003-bigquery-dynamic-schema-with-mock-fallback.md).
* *Why SQLite over Cloud SQL for prototype?* Evaluated in [ADR-0004](../adr/0004-sqlite-local-storage-vs-cloudsql.md).
* *Why local Presidio logic over Cloud DLP?* Evaluated in [ADR-0005](../adr/0005-presidio-pii-masking-vs-cloud-dlp.md).
* *Why configurable Flash family?* Evaluated in [ADR-0006](../adr/0006-configurable-gemini-flash-and-rate-limit-backoff.md).
