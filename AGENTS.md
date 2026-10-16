# Opsfleet Retail Assistant — Agent Guidelines & Execution Protocol

Status: Active  
Owner: Rudolfo Félix (AI Engineer Candidate)  
Audience: AI Coding Agents (Codex, Claude, Cursor, Antigravity)  
Last updated: 2026-10-16  

This document is the **primary instruction file** for any autonomous coding agent operating in this repository.

---

## 🧭 1. Start Here (Mandatory Context)

Before writing any code or modifying documentation, you MUST read the following foundational documents:

1. **[Product Requirements Document](docs/prd/PRD-RETAIL-ASSISTANT.md):** Business objectives, executive personas (Sarah, Marcus, David), and functional/non-functional requirements.
2. **[Technical Specification (RFC-001)](docs/rfc/RFC-001-agentic-data-assistant.md):** Complete engineering design, `AgentState` schema, StateGraph transitions, and error handling.
3. **[Retail Domain Ontology & Ubiquitous Language](docs/architecture/01_BUSINESS_ONTOLOGY_AND_UBIQUITOUS_LANGUAGE.md):** Bounded contexts, deterministic metric formulas (Net Revenue, Churn, Margin), and master acronyms.
4. **[Architecture Decision Records (ADRs)](docs/adr/README.md):** Immutable technical decisions:
   - [ADR-0001](docs/adr/0001-adopt-langgraph-state-machine.md): LangGraph state machine.
   - [ADR-0002](docs/adr/0002-adopt-langfuse-oss-for-observability.md): Langfuse OSS for observability.
   - [ADR-0003](docs/adr/0003-bigquery-dynamic-schema-with-mock-fallback.md): BigQuery dynamic schema + offline mock engine.
   - [ADR-0004](docs/adr/0004-sqlite-local-storage-vs-cloudsql.md): SQLite local store for prototype.
   - [ADR-0005](docs/adr/0005-presidio-pii-masking-vs-cloud-dlp.md): Presidio / regex PII masking.
   - [ADR-0006](docs/adr/0006-configurable-gemini-flash-and-rate-limit-backoff.md): Configurable Gemini Flash family & HTTP 429 backoff.
   - [ADR-0007](docs/adr/0007-domain-driven-semantic-layer-for-text-to-sql.md): Domain-Driven semantic layer for SQL precision.
5. **[Operational Master Plan](docs/MASTER_PLAN.md):** Full Slack alignment with Harry (PM) and Vlad Bondarenko (Tech Lead), C4 diagrams, regulatory mapping, and the Priority 0 Checklist.
6. **[Delivery Backlog Index](tickets/README.md):** Kanban tracking for tickets `OPS-001` through `OPS-007`.

---

## 🛡️ 2. Core Architectural Invariants (Non-Negotiables)

1. **The 2-Minute Evaluator Rule:** Evaluator Vlad Bondarenko will clone the repository, populate `GEMINI_API_KEY` in `.env`, and execute `python main.py` in under 2 minutes. The application must NEVER crash due to missing dependencies, unhandled exceptions, or unconfigured cloud environments.
2. **Model Selection & Configurability (Vlad Directive):**
   - The model MUST be configurable via `MODEL_NAME` in `.env`, defaulting to `gemini-2.5-flash`.
   - Swappable to `gemini-2.5-flash-lite`, `gemini-3.1-flash`, etc.
   - NEVER hardcode `gemini-1.5` (retired) or `gemini-pro` (excluded from free tier).
3. **Rate Limit Resilience:** All Gemini API invocations must be wrapped in an exponential backoff retry loop with jitter handling HTTP 429 (`RESOURCE_EXHAUSTED`). Render clean terminal progress rather than unhandled tracebacks.
4. **Call Budget Discipline:** Total LLM invocations per user question must stay strictly between **2 and 5 calls**, conforming to Vlad's free-tier guidance.
5. **Dual BigQuery Engine (Live + Offline Mock Fallback):**
   - If GCP Application Default Credentials (ADC) or a billing project are present, connect to live `bigquery-public-data.thelook_ecommerce`.
   - If GCP credentials are NOT present, automatically fall back to the built-in offline mock engine (`src/bq/mock_engine.py`) containing realistic tables (`orders`, `order_items`, `products`, `users`). Evaluators must be able to run queries out of the box with zero GCP setup.
6. **Enterprise PII Redaction:** Scrub all sensitive fields (`email`, `first_name`, `last_name`, `ip_address`) from terminal display and synthesized reports.
7. **High-Stakes Oversight (EU AI Act Art. 14):** Destructive actions (e.g. deleting saved reports) MUST pause and require explicit human confirmation (`[y/N]`) before committing.
8. **Self-Correction Cap:** SQL retry loop is strictly capped at $\le 2$ attempts to prevent infinite loops and quota drain.

---

## 📦 3. Execution Plan & Delivery Milestones

Implement the repository milestone by milestone according to the ticket backlog:

| Milestone | Ticket File | Description | Core Artifacts |
|---|---|---|---|
| **OPS-001** | [`tickets/OPS-001-environment-scaffolding.md`](tickets/OPS-001-environment-scaffolding.md) | Python environment, dependencies, `.env.example`, Pydantic settings. | `requirements.txt`, `.env.example`, `src/config.py` |
| **OPS-002** | [`tickets/OPS-002-bigquery-schema-client.md`](tickets/OPS-002-bigquery-schema-client.md) | BigQuery client, dynamic schema introspection, and offline mock fallback engine. | `src/bq/client.py`, `src/bq/schema.py`, `src/bq/mock_engine.py` |
| **OPS-003** | [`tickets/OPS-003-langgraph-self-correction.md`](tickets/OPS-003-langgraph-self-correction.md) | LangGraph StateGraph, GoogleSQL generator with ONT-001 ontology rules, self-correction loop ($\le 2$). | `src/agent/state.py`, `src/agent/graph.py`, `src/agent/sql_gen.py`, `src/agent/self_correct.py` |
| **OPS-004** | [`tickets/OPS-004-pii-masking-guardrails.md`](tickets/OPS-004-pii-masking-guardrails.md) | Deterministic Presidio / regex PII masking and user brand row-level scoping. | `src/guardrails/pii.py`, `src/guardrails/scoping.py` |
| **OPS-005** | [`tickets/OPS-005-saved-reports-hitl.md`](tickets/OPS-005-saved-reports-hitl.md) | Local SQLite persistence for saved reports and HITL deletion confirmation interrupt. | `src/storage/reports.py`, `src/agent/hitl.py` |
| **OPS-006** | [`tickets/OPS-006-rich-cli-observability.md`](tickets/OPS-006-rich-cli-observability.md) | Rich interactive terminal chat UI, spinners, OTel GenAI telemetry, and rate-limit backoff. | `main.py`, `src/cli.py`, `src/telemetry/tracer.py` |
| **OPS-007** | [`tickets/OPS-007-production-hld.md`](tickets/OPS-007-production-hld.md) | Comprehensive enterprise High-Level Design covering all 8 production requirements with C4 diagrams. | `docs/HLD.md` |

---

## 🧪 4. Testing & Verification Rules

- After completing each milestone, create and execute automated unit tests in `tests/`.
- Ensure clean code formatting and 100% type annotations.
- Update `tickets/README.md` and mark the ticket status as `done`.
- Commit with conventional format: `git commit -m "<PREFIX>-XXX <type>: <short summary>"`.
