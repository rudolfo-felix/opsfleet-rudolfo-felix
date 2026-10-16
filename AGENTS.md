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
6. **[Delivery Backlog Index](tickets/README.md):** Kanban tracking for tickets `OPS-001` through `OPS-010`.

---

## 🛡️ 2. Core Architectural Invariants & Technical Mitigations

1. **The 2-Minute Evaluator Rule:** Evaluator Vlad Bondarenko will clone the repository, populate `GEMINI_API_KEY` in `.env`, and execute `python main.py` in under 2 minutes. The application must NEVER crash due to missing dependencies, unhandled exceptions, or unconfigured cloud environments.
2. **Model Selection & Configurability (Vlad Directive):**
   - The model MUST be configurable via `MODEL_NAME` in `.env`, defaulting to `gemini-2.5-flash`.
   - Swappable to `gemini-2.5-flash-lite`, `gemini-3.1-flash`, etc.
   - NEVER hardcode `gemini-1.5` (retired) or `gemini-pro` (excluded from free tier).
3. **Rate Limit Resilience:** All Gemini API invocations must be wrapped in an exponential backoff retry loop with jitter handling HTTP 429 (`RESOURCE_EXHAUSTED`). Render clean terminal progress rather than unhandled tracebacks.
4. **Call Budget Discipline:** Total LLM invocations per user question must stay strictly between **2 and 5 calls**, conforming to Vlad's free-tier guidance.
5. **Dual BigQuery Engine (Live + DuckDB Offline Mock Fallback):**
   - If GCP Application Default Credentials (ADC) or a billing project are present, connect to live `bigquery-public-data.thelook_ecommerce`.
   - If GCP credentials are NOT present, automatically fall back to the built-in offline in-memory **DuckDB engine** (`src/bq/mock_engine.py`) containing realistic tables (`orders`, `order_items`, `products`, `users`). Evaluators must be able to run queries out of the box with zero GCP setup.
6. **Table Qualification Sanitizer (Mitigation 1):** Pre-execution sanitizer automatically ensures all table references are fully qualified (`` `bigquery-public-data.thelook_ecommerce.<table_name>` ``) and temporal intervals conform to BigQuery standard syntax.
7. **Conditional Brand Scoping (Mitigation 2):** Scoping guard injects brand filters for transactional/product queries, while cleanly handling pure demographic `users` queries without invalid column errors.
8. **Empty Result Diagnostic Feedback (Mitigation 3):** The self-correction loop catches queries returning 0 rows due to case-sensitivity or restrictive filters and suggests corrective adjustments.
9. **Enterprise PII Redaction:** Scrub all sensitive fields (`email`, `first_name`, `last_name`, `ip_address`) from terminal display and synthesized reports.
10. **High-Stakes Oversight with Checkpointer (Mitigation 5):** Destructive actions (e.g. deleting saved reports) halt graph execution via LangGraph `MemorySaver` `interrupt()` and require explicit human confirmation (`[y/N]`) before committing.
11. **Self-Correction Cap:** SQL retry loop is strictly capped at $\le 2$ attempts to prevent infinite loops and quota drain.
12. **Evidence-Based Verification Gate (No-Mistakes Protocol):** Autonomous agents must persist concrete execution evidence (pytest execution outputs, mock query results, PII-scrubbed samples) to `tests/evidence/` for every ticket before completion.
13. **Zero Dev-Cost Bias (Enterprise Quality Bar):** Autonomous coding agents must never sacrifice architectural robustness (typed Pydantic schemas, explicit error hierarchies, resilience decorators) under the assumption that enterprise patterns take too long. Quality and resilience are non-negotiable.
14. **Autonomous Swarm Review & Auto-Progression Gate:** Every ticket requires an atomic RFC (`RFC-OPS-XXX.md`) audited and approved by independent subagent Reviewer 1 (and Reviewer 2 if confidence < 90% or ticket is Critical: OPS-004, OPS-006, OPS-010 per [`docs/architecture/AUTONOMOUS_SWARM_PROTOCOL.md`](docs/architecture/AUTONOMOUS_SWARM_PROTOCOL.md)). Upon code completion and pytest passing, an independent QA/PO subagent issues `docs/qa/QA_REVIEW_OPS-XXX.md`. Once cleared, the agent automatically commits, merges to main, pushes, and advances to the next ticket in the DAG without waiting for manual human intervention.

---

## 📦 3. Execution Plan & Delivery Milestones

Implement the repository milestone by milestone according to the ticket backlog:

| Milestone | Ticket File | Description | Core Artifacts |
|---|---|---|---|
| **OPS-000** | [`tickets/OPS-000-foundation-and-planning.md`](tickets/OPS-000-foundation-and-planning.md) | Project foundation, PRD, RFC-001, 7 ADRs, ONT-001 Domain Ontology & L8 Audit (`done`). | `PRD`, `RFC-001`, `ONT-001`, `docs/adr/`, `MASTER_PLAN.md` |
| **OPS-001** | [`tickets/OPS-001-scaffolding-config-resilience.md`](tickets/OPS-001-scaffolding-config-resilience.md) | Python environment, dependencies, `.env.example`, Pydantic settings & 429 backoff decorator. | `pyproject.toml`, `requirements.txt`, `.env.example`, `src/config.py`, `src/agent/resilience.py`, `tests/conftest.py` |
| **OPS-002A** | [`tickets/OPS-002A-bigquery-live-client.md`](tickets/OPS-002A-bigquery-live-client.md) | BigQuery client, dynamic schema introspection, caching & table qualification sanitizer. | `src/bq/client.py`, `src/bq/schema.py` |
| **OPS-002B** | [`tickets/OPS-002B-offline-mock-duckdb-engine.md`](tickets/OPS-002B-offline-mock-duckdb-engine.md) | In-memory DuckDB offline mock engine with synthetic e-commerce fixtures & auto-fallback. | `src/bq/mock_engine.py` |
| **OPS-003** | [`tickets/OPS-003-langgraph-state-and-sql-generator.md`](tickets/OPS-003-langgraph-state-and-sql-generator.md) | `AgentState` schema, domain few-shot prompts & GoogleSQL generation node with ONT-001 rules. | `src/agent/state.py`, `src/agent/prompts.py`, `src/agent/nodes/generate_sql.py` |
| **OPS-004** | [`tickets/OPS-004-sql-execution-and-self-correction.md`](tickets/OPS-004-sql-execution-and-self-correction.md) | SQL execution runner, self-correction reflection node, empty result handling & circuit breaker ($\le 2$). | `src/agent/nodes/execute_sql.py`, `src/agent/nodes/self_correct.py`, `src/agent/graph.py` |
| **OPS-005** | [`tickets/OPS-005-executive-report-synthesizer.md`](tickets/OPS-005-executive-report-synthesizer.md) | Executive insight & Q2 action item synthesizer node tailored to Sarah (CEO / VP). | `src/agent/nodes/synthesize.py` |
| **OPS-006** | [`tickets/OPS-006-enterprise-pii-and-brand-scoping.md`](tickets/OPS-006-enterprise-pii-and-brand-scoping.md) | Deterministic Presidio / regex PII masking and user brand row-level scoping guardrails. | `src/guardrails/pii.py`, `src/guardrails/scope.py` |
| **OPS-007** | [`tickets/OPS-007-saved-reports-and-hitl-interrupt.md`](tickets/OPS-007-saved-reports-and-hitl-interrupt.md) | Local SQLite persistence for saved reports and EU AI Act HITL deletion confirmation interrupt. | `src/storage/reports.py`, `src/agent/nodes/reports.py` |
| **OPS-008** | [`tickets/OPS-008-opentelemetry-genai-tracing.md`](tickets/OPS-008-opentelemetry-genai-tracing.md) | OpenTelemetry GenAI semantic tracing, node latency, and 2–5 call budget tracker. | `src/telemetry/tracer.py` |
| **OPS-009** | [`tickets/OPS-009-rich-cli-interface-and-main.md`](tickets/OPS-009-rich-cli-interface-and-main.md) | Rich interactive terminal chat UI, telemetry panel, and `main.py` entrypoint. | `main.py`, `src/cli/view.py`, `src/cli/tables.py` |
| **OPS-010** | [`tickets/OPS-010-production-hld-and-20-battery-runner.md`](tickets/OPS-010-production-hld-and-20-battery-runner.md) | Comprehensive enterprise High-Level Design (HLD) with C4 diagrams and 20-battery test runner. | `README.md`, `docs/HLD.md`, `scripts/verify_batteries.py` |

---

## 🧪 4. Testing & Verification Rules

- After completing each milestone, create and execute automated unit tests in `tests/`.
- Ensure clean code formatting and 100% type annotations.
- Update `tickets/README.md` and mark the ticket status as `done`.
- Commit with conventional format: `git commit -m "<PREFIX>-XXX <type>: <short summary>"`.
