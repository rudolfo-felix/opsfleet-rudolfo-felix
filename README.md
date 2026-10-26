# Opsfleet AI Technical Assignment: Retail Data Analysis Chat Assistant

**Candidate:** Eng. Rudolfo Valentino Marques Félix  
**Position:** AI Engineer (Opsfleet)  
**Repository:** [github.com/rudolfo-felix/opsfleet-rudolfo-felix](https://github.com/rudolfo-felix/opsfleet-rudolfo-felix)  
**Slack Channel:** `#t-ai-rudolfo-félix`  
**Production High-Level Design (HLD):** [docs/HLD.md](docs/HLD.md)  
**Delivery Backlog:** [tickets/README.md](tickets/README.md) (All 12 Tickets OPS-000 to OPS-011 Completed)

---

## ⚡ 2-Minute Evaluator Quickstart (Invariant 1 Compliance)

This repository is strictly engineered to satisfy the **2-Minute Clone-and-Run Evaluator Rule**. Evaluators do **not** require GCP credentials, billing setups, or external telemetry infrastructure to execute the full system. The local DuckDB engine transparently provides complete offline parity with GoogleSQL on the `thelook_ecommerce` dataset.

```bash
# 1. Clone repository
git clone https://github.com/rudolfo-felix/opsfleet-rudolfo-felix.git
cd opsfleet-rudolfo-felix

# 2. Setup Python 3.11 virtual environment & install package
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# 3. Pre-Flight Configuration Verification (Exits 0 without API key or external calls)
python main.py --dry-run

# 4. Run the 20 Pre-Delivery Test Batteries (Triple Verification Protocol)
python scripts/verify_batteries.py

# 5. Run the 100 Hermetic Unit & Integration Tests
pytest -v
```

### Running with Gemini LLM
To execute interactive conversational analytics with Google Gemini, set your API key (available free with high rate-limits at [Google AI Studio](https://aistudio.google.com/)):

```bash
export GEMINI_API_KEY="AIzaSy..."

# Launch interactive CLI session in offline mock mode (zero GCP setup required)
python main.py --mock-bq

# Or launch against live Google Cloud BigQuery
python main.py
```

---

## 🏛️ System Architecture Overview

The system is architected as an enterprise-grade, stateful AI Data Assistant governed by **Domain-Driven Design (DDD)**, an explicit **Ontology layer (ONT-001)**, and cyclic LangGraph state machines with self-correcting feedback loops.

```
                  ┌──────────────────────────────────────────────┐
                  │           User Natural Language Query        │
                  └──────────────────────┬───────────────────────┘
                                         │
                                         ▼
                            ┌────────────────────────┐
                            │  intent_classifier     │
                            └────┬──────────────┬────┘
                 Analytical Query│              │Destructive / Storage
                                 ▼              ▼
                     ┌─────────────────┐  ┌────────────────────┐
                     │  generate_sql   │  │   reports_node     │
                     └────────┬────────┘  │ (SQLite Storage &  │
                              │           │  HITL Interrupt)   │
                              ▼           └─────────┬──────────┘
                     ┌─────────────────┐            │
          ┌─────────►│   execute_sql   │            │
          │          └────────┬────────┘            │
          │                   │                     │
          │       Compiler /  │ Success / Rows      │
          │       0-Rows Error│                     │
          │                   ▼                     ▼
┌──────────────────┐ ┌─────────────────┐  ┌────────────────────┐
│   self_correct   │ │  sanitize_pii   │  │   Human-in-the-    │
│ (Reflective Loop │ │ (Presidio RegEx │  │   Loop Interrupt   │
│   capped <= 2)   │ │  Masking Gate)  │  │ (EU AI Act Art 14) │
└──────────────────┘ └────────┬────────┘  └────────────────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │   synthesize    │
                     │ (3 H2 Sections) │
                     └────────┬────────┘
                              │
                              ▼
                  ┌───────────────────────┐
                  │ Rich Terminal Output  │
                  └───────────────────────┘
```

For complete enterprise specifications including GCP C4 Level 1–3 diagrams, BIRD-SQL evaluation benchmarks, Universal Commerce Protocol (UCP) alignment, and BigQuery RLS/DDM controls, read the **[Production High-Level Design (HLD)](docs/HLD.md)**.

---

## 💻 CLI Flags & Configuration Reference

The CLI entrypoint (`main.py`) provides exhaustive configuration options for role-based testing and multi-tenant isolation:

| CLI Option | Default | Environment Variable | Description |
|---|---|---|---|
| `--user-id` | `sarah_ceo` | N/A | Active session user persona identifier (e.g. `sarah_ceo`, `marcus_buyer`). |
| `--brands` | `None` | N/A | Comma-separated list of brand restrictions enforcing multi-tenant catalog scoping. |
| `--model` | `gemini-2.5-flash` | `MODEL_NAME` | Gemini LLM model identifier (`gemini-2.5-flash` or `gemini-2.5-flash-lite`). |
| `--mock-bq` | `False` | `MOCK_BIGQUERY` | Force offline execution using in-memory DuckDB engine and synthetic fixtures. |
| `--dry-run` | `False` | N/A | Execute pre-flight dependency & state graph verification and exit cleanly (code 0). |

---

## 🎯 Real-World Analytical Prompt Recipes

Test the agent interactively with these retail queries aligned with the Retail Ubiquitous Language ([ONT-001](docs/architecture/01_BUSINESS_ONTOLOGY_AND_UBIQUITOUS_LANGUAGE.md)):

### 1. Executive Net Revenue
> *"What is our Net Revenue by product category for Q1 2024?"*  
**Ontology Enforcement:** Automatically injects `status NOT IN ('Cancelled', 'Returned')` and aggregates `sale_price` from `order_items`.

### 2. Trailing 90-Day Churn Inactivity
> *"How many active customers do we have based on orders in the last 90 days?"*  
**Temporal Math:** Utilizes `TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAY)` against `orders.created_at` avoiding non-existent churn columns.

### 3. Gross Margin by Brand
> *"Calculate the gross profit margin percentage across all brands."*  
**Precision Math:** Robustly generates `SAFE_DIVIDE(SUM(sale_price - cost), SUM(sale_price)) * 100` preventing division-by-zero crashes.

### 4. Multi-Tenant Brand Scoping (Category Manager Persona)
```bash
python main.py --mock-bq --user-id "marcus-lead" --brands "Calvin Klein,Tommy Hilfiger"
```
> *"Show me our best selling products by units sold."*  
**Automated Scope Guardrail:** Injects `WHERE products.brand IN ('Calvin Klein', 'Tommy Hilfiger')` automatically into the generated SQL. Pure demographic user queries remain conditionally exempted ([Mitigation 2](docs/rfc/RFC-OPS-006-enterprise-pii-and-brand-scoping.md)).

### 5. Report Persistence & Destructive Operations (HITL Oversight)
> *"Save the last executive briefing as 'Q1 Category Performance'"*  
> *"List all saved executive reports"*  
> *"Delete saved report 1"*  
**Article 14 Human Oversight:** Pauses execution state via LangGraph `interrupt()`, demanding interactive `[y/N]` confirmation before executing hard database deletion.

---

## 🧪 20 Pre-Delivery Test Batteries (Triple Verification Gate)

Every component is validated across a **Triple Verification Protocol** (Pass 1: Developer verification, Pass 2: Clean-room evaluation, Pass 3: Adversarial stress test) executed via `scripts/verify_batteries.py`:

| Battery ID | Category | Description | Triple Verification Status |
|---|---|---|---|
| **TB-01** | Evaluator Quickstart | 2-Minute clone-and-run without API keys (`--dry-run`) | **100% PASS** (3/3) |
| **TB-02** | BigQuery Fallback | Offline DuckDB parity on thelook_ecommerce | **100% PASS** (3/3) |
| **TB-03** | GoogleSQL Translation | Normalizes intervals, backticks, `DATE_TRUNC`, `SAFE_DIVIDE` | **100% PASS** (3/3) |
| **TB-04** | Read-Only Safety | Rejects `DROP`, `DELETE`, `UPDATE`, `;` query chaining | **100% PASS** (3/3) |
| **TB-05** | Domain Analytics (ONT-001) | Net Revenue excludes Cancelled & Returned orders | **100% PASS** (3/3) |
| **TB-06** | Domain Analytics (ONT-001) | Trailing 90-day churn inactivity temporal math | **100% PASS** (3/3) |
| **TB-07** | Domain Analytics (ONT-001) | Gross Margin calculated via `SAFE_DIVIDE` | **100% PASS** (3/3) |
| **TB-08** | Executive Synthesis | 3 mandatory H2 sections with business actions | **100% PASS** (3/3) |
| **TB-09** | Enterprise PII Scrubbing | In-process redaction: name, email, IP address | **100% PASS** (3/3) |
| **TB-10** | Enterprise Guardrails | Brand catalog scoping enforced for category managers | **100% PASS** (3/3) |
| **TB-11** | Mitigation 2 Guardrail | Pure user queries exempted from invalid brand syntax | **100% PASS** (3/3) |
| **TB-12** | High-Stakes Governance | HITL interrupt pauses on destructive report deletion | **100% PASS** (3/3) |
| **TB-13** | High-Stakes Governance | Resumption with confirmation commits purge | **100% PASS** (3/3) |
| **TB-14** | Self-Healing Reflection | Compiler error feedback loop self-corrects SQL | **100% PASS** (3/3) |
| **TB-15** | FinOps & Resilience | Circuit breaker hard-caps self-correction at $\le 2$ retries | **100% PASS** (3/3) |
| **TB-16** | Cloud Limits Resilience | HTTP 429 exponential jitter backoff handles rate limits | **100% PASS** (3/3) |
| **TB-17** | FinOps Accounting | Programmatic enforcement of Vlad's 2–5 calls budget | **100% PASS** (3/3) |
| **TB-18** | Enterprise Architecture | C4 Model Levels 1, 2, 3 diagrams validated in HLD | **100% PASS** (3/3) |
| **TB-19** | Quality & Compliance | 178 markdown links verified with 0 broken links | **100% PASS** (3/3) |
| **TB-20** | Quality & Compliance | Clean git tree & 100% commit traceability verified | **100% PASS** (3/3) |

---

## 📂 Repository Contents & Documentation Map

* 📄 **[Production High-Level Design (HLD)](docs/HLD.md):** Formal enterprise architecture document covering all 8 assignment requirements, C4 Level 1–3 diagrams, Presidio vs Cloud DLP trade-offs, and FinOps TCO calculations.
* 📑 **[Master Documentation Index](docs/README.md):** Complete technical documentation map and reading order.
* 🎫 **[Delivery Backlog & Sprints](tickets/README.md):** Granular delivery backlog (OPS-000 to OPS-011) with user stories, acceptance criteria, and PR mapping.
* 📋 **[Product Requirements Document (PRD)](docs/prd/PRD-RETAIL-ASSISTANT.md):** Business objectives, executive personas, and functional specifications.
* 📐 **[Technical Specification (RFC-001)](docs/rfc/RFC-001-agentic-data-assistant.md):** Engineering design, LangGraph StateGraph schema, and error-handling pipelines.
* 🏛️ **[Retail Domain Ontology & Ubiquitous Language (DDD)](docs/architecture/01_BUSINESS_ONTOLOGY_AND_UBIQUITOUS_LANGUAGE.md):** Canonical entities (`Customer`, `Order`, `Product`), metric calculation rules, and master acronyms glossary eliminating Text-to-SQL semantic ambiguity.
* 🏛️ **[Architecture Decision Records (ADRs)](docs/adr/README.md):** MADR-standard decision logs (ADR 0001 through 0007) capturing trade-offs, consequences, and design choices.
* 📑 **[Master Execution Plan & Checklist](docs/MASTER_PLAN.md):** Operational blueprint, verbatim Slack Q&A alignment with Harry (AI PM) & Vlad (AI Tech Lead), and regulatory mapping.
* 🛡️ **[Model Allocation & Failure Resilience](docs/architecture/09_MODEL_ALLOCATION_AND_FAILURE_RESILIENCE.md):** Token allocation matrix and enterprise failure resilience patterns.
* 📜 **[Genesis & Prompt Orchestration Log](docs/templates/GENESIS_SETUP_PROMPT.md):** Complete four-stage prompt lifecycle, autonomous swarm trigger prompt, critical human steering prompt, and multi-model OpenAI Codex review log.
* 💰 **FinOps & Dependency Strategy:** Explicit **Free/OSS-first evaluation stack** (100% runnable at $0.00 cost) vs. Scalable Enterprise Cloud Trade-offs (Langfuse vs. LangSmith, SQLite vs CloudSQL, Presidio vs Cloud DLP).
* 🛡️ **Regulatory & Standards Alignment:** Comprehensive mapping of safety, HITL oversight, and risk controls to the **EU AI Act (Article 14)** and **NIST AI RMF (NIST AI 600-1)**.
* 📚 **Architectural Foundations & Reference Whitepapers:**
  * [The Agentic Operating Model (LangChain Whitepaper)](docs/assets/The%20Agentic%20Operating%20Model.pdf) — Enterprise blueprint for the Agent Development Lifecycle (ADLC), LangGraph stateful execution, HITL interrupts, and agentic governance.
* 📦 **Original Assessment PDFs:**
  * [AI Technical Assignment - Retail Company.pdf](docs/assets/AI%20Technical%20Assignment%20-%20Retail%20Company.pdf)
  * [AI Engineer Opsfleet.pdf](docs/assets/AI%20Engineer%20Opsfleet.pdf)

---

## 🏆 Delivery Milestones (100% Complete)

| Story ID | Sprint Title | Status | RFC & Review Clearance | Unit Tests |
|---|---|---|---|---|
| **OPS-000** | Master Plan, PRD, RFC-001, ONT-001 & ADRs 0001–0007 | `done` | [RFC-001](docs/rfc/RFC-001-agentic-data-assistant.md) · [L8 Audit](docs/architecture/L8_PRINCIPAL_AUDIT_REPORT.md) | N/A (Spec) |
| **OPS-001** | Config, Settings Validation & Exponential Rate-Limit Backoff | `done` | [RFC-OPS-001](docs/rfc/RFC-001-agentic-data-assistant.md) · [QA Review](docs/qa/QA_REVIEW_OPS-002B.md) | 12 Passed |
| **OPS-002A** | Live BigQuery Client, TTL Schema Cache & Qualification Sanitizer | `done` | [RFC-001](docs/rfc/RFC-001-agentic-data-assistant.md) · [ADR-0003](docs/adr/0003-bigquery-dynamic-schema-with-mock-fallback.md) | 16 Passed |
| **OPS-002B** | Offline Mock DuckDB Engine, Dialect Adapter & Synthetic Fixtures | `done` | [RFC-OPS-002B](docs/rfc/RFC-OPS-002B-offline-mock-duckdb-engine.md) · [QA Review](docs/qa/QA_REVIEW_OPS-002B.md) | 15 Passed |
| **OPS-003** | LangGraph State Schema & GoogleSQL Generator (ONT-001 Rules) | `done` | [RFC-OPS-003](docs/rfc/RFC-OPS-003-langgraph-state-and-sql-generator.md) · [QA Review](docs/qa/QA_REVIEW_OPS-003.md) | 7 Passed |
| **OPS-004** | Execution Node, Self-Correction Feedback Loop & Circuit Breaker | `done` | [RFC-OPS-004](docs/rfc/RFC-OPS-004-sql-execution-and-self-correction.md) · [QA Review](docs/qa/QA_REVIEW_OPS-004.md) | 7 Passed |
| **OPS-005** | Executive Insight & Action Item Synthesizer (3 H2 Sections) | `done` | [RFC-OPS-005](docs/rfc/RFC-OPS-005-executive-report-synthesizer.md) · [QA Review](docs/qa/QA_REVIEW_OPS-005.md) | 5 Passed |
| **OPS-006** | Enterprise PII Scrubbing Gate & Conditional Brand Scoping | `done` | [RFC-OPS-006](docs/rfc/RFC-OPS-006-enterprise-pii-and-brand-scoping.md) · [QA Review](docs/qa/QA_REVIEW_OPS-006.md) | 14 Passed |
| **OPS-007** | Saved Reports SQLite Storage & EU AI Act HITL Interrupt | `done` | [RFC-OPS-007](docs/rfc/RFC-OPS-007-saved-reports-and-hitl-interrupt.md) · [QA Review](docs/qa/QA_REVIEW_OPS-007.md) | 5 Passed |
| **OPS-008** | OpenTelemetry GenAI Semantic Tracing & FinOps Budget Tracker | `done` | [RFC-OPS-008](docs/rfc/RFC-OPS-008-opentelemetry-genai-tracing.md) · [QA Review](docs/qa/QA_REVIEW_OPS-008.md) | 6 Passed |
| **OPS-009** | Rich Terminal UI, Spinners, Dry-Run Mode & Interactive REPL | `done` | [RFC-OPS-009](docs/rfc/RFC-OPS-009-rich-cli-interface-and-main.md) · [QA Review](docs/qa/QA_REVIEW_OPS-009.md) | 7 Passed |
| **OPS-010** | Production High-Level Design (HLD) & 20-Battery Test Runner | `done` | [RFC-OPS-010](docs/rfc/RFC-OPS-010-production-hld-and-20-battery-runner.md) · [QA Review](docs/qa/QA_REVIEW_OPS-010.md) | 20 Batteries |
| **OPS-011** | Golden Trios Knowledge Retrieval, Prompt Accuracy Frontier Benchmark & BigQueryRunner | `done` | [RFC-OPS-011](docs/rfc/RFC-OPS-011-golden-trios-and-prompt-frontier.md) · [QA Review](docs/qa/QA_REVIEW_OPS-011.md) | 6 Passed (100 total) |

* 📊 **[Empirical Model Frontier Benchmark Report (OPS-011)](docs/BENCHMARK_REPORT.md):** 5/5 Canonical Retail Queries passing on live Gemini (`gemini-3.5-flash-lite`), measuring latency, token usage, and zero syntax errors.

**Total Unit Test Battery:** 100 Hermetic Unit Tests (100% Passing) + 20 Pre-Delivery Test Batteries (100% Passing).

---

## ⏱️ Execution Timeline & Time Budget Compliance (10.0 Hours)

In strict compliance with Page 3 of the assignment specification (*"We expect this assignment to take between 6 to 12 hours of work"*), this project was executed across two focused engineering sessions totaling **10 hours and 02 minutes of active work**:

| Dimension | Day 1: Oct 15 (Architecture & Spec) | Day 2: Oct 16 (Swarm Delivery & Frontier) | Total Project Effort | Opsfleet Target Window |
|---|:---:|:---:|:---:|:---:|
| **Active Engineering Time** | **2h 42m** | **7h 20m** | **10h 02m** | **6 – 12 hours** |
| **Wall-Clock Window** | 08:06 – 12:58 (4h 52m) | 10:47 – 19:11 (8h 23m) | 13h 15m | 1-week window |
| **Antigravity Trajectory Steps** | 511 steps | 2,395 steps | **2,906 steps** | Autonomous Multi-Agent |
| **Direct User Turns / Prompts** | 32 prompts | 31 prompts | **63 prompts** | Captain & Crew Steering |
| **Autonomous Subagents Spawned** | 0 subagents | 21 subagents | **21 subagents** | Peer Review & PO Auditing |
| **Git Commits & Traceability** | 11 commits | 19 commits | **30 commits** | 100% Story Traceability |
| **Verification Gate** | Spec & ADRs | 100 Tests / 20 Batteries | **100% Green** | Triple Verification Gate |

*For the complete 4-stage prompt engineering log, autonomous swarm prompts, and multi-model review audit, see [Genesis & Prompt Orchestration Log](docs/templates/GENESIS_SETUP_PROMPT.md).*
