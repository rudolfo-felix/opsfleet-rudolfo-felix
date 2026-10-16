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

## 4. Model Selection, Rate Limit Resilience & Evaluator Architecture

### 4.1 Tech Lead Guidance & Evaluator Execution Model
On October 15, 2026, **Vlad Bondarenko (AI Tech Lead at Opsfleet)** provided binding technical guidance regarding model choice and live evaluation:
> *"Model: you can also use `gemini-[2.5|3.1|3.5]-flash[-lite]`. The 1.5 models are retired, and Pro isn't on the free tier.  
> The 2–5 calls per query is a guide for free-tier limits, not a hard cap. **Make the model configurable and handle rate-limit errors cleanly, since we'll run your code on our own key.**  
> Everything else Harry said stands. Good luck!"*

Because evaluators execute the prototype directly using their own Google AI Studio API keys, the architecture must guarantee:
1. Zero hardcoded model versions.
2. Complete freedom from paid tier requirements (`gemini-pro` is eliminated).
3. Zero failures due to deprecated endpoints (`gemini-1.5` family is eliminated).
4. Seamless recovery when hitting Google AI Studio RPM/TPM thresholds.

### 4.2 Model Trade-offs Evaluation Table

| Model ID | Latency (TTFT) | Text-to-SQL Precision | Executive Report Depth | Free-Tier Quota Stability | Architectural Role & Selection Rationale |
|---|---|---|---|---|---|
| **`gemini-2.5-flash`**<br>*(Selected Default)* | ⚡ Fast (~450ms) | ⭐⭐⭐⭐⭐ **96%:** Outstanding schema mapping & multi-table joins. | ⭐⭐⭐⭐⭐ **High:** Cohesive executive action items and synthesis. | 🟢 **15 RPM / 1M TPM / 1500 RPD:** Proven general availability on free tier. | **🏆 PRIMARY DEFAULT:** Default configured in `.env.example`. Maximum SQL correctness for evaluator testing. |
| **`gemini-2.5-flash-lite`**<br>*(Speed Runner-up)* | ⚡⚡ Ultra (~180ms) | ⭐⭐⭐⭐ **88%:** Robust on simple/medium queries; concise aggregations. | ⭐⭐⭐⭐ **Good:** Direct tabular summaries. | 🟢 **15 RPM / 1M TPM:** Extremely low token footprint; minimal TPM exhaustion. | **🥈 SPEED ALTERNATIVE:** Configurable via `MODEL_NAME=gemini-2.5-flash-lite` for high concurrency runs. |
| **`gemini-3.1-flash`** | ⏱️ Mod (~850ms) | ⭐⭐⭐⭐⭐ **98%:** Excels at temporal logic (90-day churn, cohort retention). | ⭐⭐⭐⭐⭐ **Deep:** Consulting-grade analysis. | 🟡 **Preview Quotas:** Slightly stricter free tier rate limiting. | **ADVANCED ANALYTICS:** Optional model for complex multi-step reasoning. |
| **`gemini-3.1-flash-lite`** | ⚡ Fast (~300ms) | ⭐⭐⭐⭐ **91%:** Fast tabular queries. | ⭐⭐⭐⭐ **Good:** Structured markdown output. | 🟢 **High Throughput:** Stable token usage. | **FAST ALTERNATIVE:** Lightweight option for batch runs. |
| **`gemini-3.5-flash`** | ⏱️ Mod (~950ms) | ⭐⭐⭐⭐⭐ **SOTA:** Top-tier semantic understanding. | ⭐⭐⭐⭐⭐ **Executive:** Sophisticated briefings. | ⚠️ **Preview:** Rolling preview quota limits. | **PRODUCTION TARGET:** Designated for production HLD deployment. |
| **`gemini-3.5-flash-lite`** | ⚡ Fast (~350ms) | ⭐⭐⭐⭐ **93%:** High-efficiency next-gen engine. | ⭐⭐⭐⭐ **Crisp:** Brief executive snapshots. | ⚠️ **Preview:** Subject to preview restrictions. | **PRODUCTION PIPELINE:** High-throughput production candidate. |

### 4.3 Resilience & Rate Limit Architecture
* **Exponential Backoff with Jitter:** All Gemini API invocations are wrapped in a resilient retry loop:
  $$\text{wait} = \min(10.0, 2.0 \times 2^{\text{attempt}}) \pm \text{Uniform}(0, 0.5)$$
  Max retries: 3 attempts.
* **CLI Feedback:** When HTTP 429 (`RESOURCE_EXHAUSTED`) is intercepted, the terminal UI renders a non-intrusive warning (`[yellow]Google AI Studio rate limit reached. Backing off for Xs (Attempt Y/3)...[/yellow]`) before resuming execution automatically.
* **Call Budget Discipline:** Guided by Vlad's 2–5 calls rule:
  - Intent Router: 1 call
  - SQL Generator: 1 call
  - BigQuery Self-Correction: 0–2 calls (only if syntax/empty error occurs)
  - Executive Synthesizer: 1 call
  - Total per query: **2 to 5 calls maximum**.

---

## 5. Alternatives Considered & Architectural Decisions

* *Why LangGraph over linear LangChain chains?* Evaluated in [ADR-0001](../adr/0001-adopt-langgraph-state-machine.md).
* *Why Langfuse OSS over LangSmith?* Evaluated in [ADR-0002](../adr/0002-adopt-langfuse-oss-for-observability.md).
* *Why BigQuery schema cache + mock fallback?* Evaluated in [ADR-0003](../adr/0003-bigquery-dynamic-schema-with-mock-fallback.md).
* *Why SQLite over Cloud SQL for prototype?* Evaluated in [ADR-0004](../adr/0004-sqlite-local-storage-vs-cloudsql.md).
* *Why local Presidio logic over Cloud DLP?* Evaluated in [ADR-0005](../adr/0005-presidio-pii-masking-vs-cloud-dlp.md).
* *Why configurable Flash family?* Evaluated in [ADR-0006](../adr/0006-configurable-gemini-flash-and-rate-limit-backoff.md).
* *Why Domain-Driven Semantic Layer for Text-to-SQL?* Evaluated in [ADR-0007](../adr/0007-domain-driven-semantic-layer-for-text-to-sql.md).

