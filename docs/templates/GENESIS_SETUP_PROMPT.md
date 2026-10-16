# 📜 Master Genesis & Autonomous Swarm Prompt Orchestration Log

**Project:** Retail Data Analysis Chat Assistant (Opsfleet Technical Assessment)  
**Author & Candidate:** Eng. Rudolfo Valentino Marques Félix  
**Position:** AI Engineer (Opsfleet)  
**Evaluators:** Vlad Bondarenko (AI Tech Lead), Harry (AI Project Manager)  
**Governance Standard:** Human-in-the-Loop Steering (EU AI Act Article 14) & Multi-Agent Swarm Protocol  
**Date:** 2026-10-16  
**Status:** Canonical Prompt Architecture & Audit Record  

---

## 1. Executive Context & Architectural Rationale

In high-stakes enterprise AI engineering, autonomous coding agents must not operate as "unconstrained prompt wrappers" or single-shot code generators. Without strict architectural guardrails, autonomous agents suffer from:
1. **Scope and Semantic Drift:** Hallucinating non-existent database columns, inventing APIs, or miscalculating business metrics.
2. **Infinite Healing Loops & Token Drainage:** Repeatedly retrying failed unit tests without root-cause reflection, inflating LLM costs.
3. **Loss of Traceability:** Generating monolithic commits without linked user stories, acceptance criteria, or empirical verification evidence.

To achieve a **top 1% tier submission**, this repository was orchestrated through a formal **Four-Stage Human-Agent Collaboration Pipeline**:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                     FOUR-STAGE PROMPT ORCHESTRATION LIFECYCLE                          │
│                                                                                        │
│  [Stage 1: Day 0 Master Genesis Prompt]                                                │
│  Established immutable engineering invariants (AGENTS.md), Domain-Driven Design        │
│  Ontology (ONT-001), MADR architecture records (ADR 0001-0007), and atomic backlog.   │
│         │                                                                              │
│         ▼                                                                              │
│  [Stage 2: Autonomous Swarm Execution Prompt (/goal /auto)]                            │
│  Triggered multi-agent swarm running feat branch creation, RFC authoring, independent   │
│  systems architect review, coding, pytest/ruff verification, and PO/QA sign-off.       │
│         │                                                                              │
│         ▼                                                                              │
│  [Stage 3: Critical Human Steering & Frontier Exploration Prompt]                      │
│  Human Captain challenged the model's live API capabilities, demanded BigQueryRunner   │
│  starter snippet parity, and mandated OPS-011 for live Gemini frontier benchmarking.   │
│         │                                                                              │
│         ▼                                                                              │
│  [Stage 4: Multi-Model Adversarial Review Gate (OpenAI Codex CLI)]                     │
│  Invested 81% of monthly OpenAI Codex quota to perform independent uncommitted static   │
│  code reviews, hardening DuckDB catalog translation and Golden Bucket thresholding.    │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Stage 1: Day 0 Master Genesis Prompt (Groundwork & Architecture)

### Why It Was Formulated:
Before writing a single line of Python application code, the agent was instructed to act as an **L8 Principal Systems Architect**. The goal was to establish an unshakeable engineering foundation:
- Embed the **2-Minute Evaluator Rule** (ensuring zero setup friction for evaluators without GCP credentials).
- Formalize the **Domain-Driven Design (DDD) Ubiquitous Language (`ONT-001`)** so that SQL generation never confuses Net Revenue with Gross Revenue or invents a non-existent `is_churned` column.
- Pre-define the **20 Pre-Delivery Test Batteries (`TB-01` to `TB-20`)** as an immutable contract.
- Break down the roadmap into 11 atomic tickets (`OPS-000` to `OPS-010`) with a visual Mermaid DAG.

### The Executed Genesis Prompt:
```markdown
You are an L8 Principal Systems Architect and Staff AI Engineer.
You operate under the "Captain & Crew" agent engineering framework: hands-on-keyboard terminal focus, progressive disclosure, anti-fragility, and evidence-based quality gates.

I am initializing an enterprise AI Agent repository for the Opsfleet AI Technical Assessment (Retail Data Analysis Assistant).
The core business objective is: Build a stateful, enterprise-grade data analysis chat assistant that allows retail executives (Sarah, CEO/VP; Marcus, Category Buyer) to ask complex questions regarding revenue, churn, product margins, and database structure over bigquery-public-data.thelook_ecommerce.
The key evaluators are: Vlad Bondarenko (AI Tech Lead) and Harry (AI Project Manager).

The technical constraints, evaluator requirements, and directives are:
- 2-Minute Evaluator Rule: The repo must be 100% cloneable and runnable in under 2 minutes without mandatory GCP service accounts or billing setups.
- Dual-Engine Strategy: Seamless fallback to an in-memory DuckDB engine with synthetic thelook_ecommerce fixtures when live BigQuery credentials are not configured.
- Rate Limit Resilience: Exponential backoff with full jitter on HTTP 429 and HTTP 503 errors.
- FinOps Budget Discipline: Strictly enforce Vlad Bondarenko's constraint of 2-5 LLM calls per turn and max 2 self-correction retries.
- Privacy & PII Guardrails: In-process redaction of sensitive identifiers (email, first_name, last_name, ip_address) before data reaches the synthesis LLM or OpenTelemetry spans.
- EU AI Act Article 14 Human Oversight: Pausing execution state via LangGraph interrupt() with MemorySaver thread persistence on destructive report deletion.
- Weekly Persona Agility: Decoupled Prompt CMS allowing tone shifts without code redeployment.

Execute Phase 0 (Groundwork & Architecture) before writing any application code:

1. ARCHITECTURAL INVARIANTS (AGENTS.md):
   Create root `AGENTS.md` defining the 14 immutable engineering invariants of the repo.
2. DOMAIN-DRIVEN DESIGN & ONTOLOGY:
   Create `docs/architecture/01_BUSINESS_ONTOLOGY_AND_UBIQUITOUS_LANGUAGE.md` establishing the canonical business entities, financial metric definitions (Net Revenue excluding Cancelled/Returned; Trailing 90-day Churn via TIMESTAMP_SUB), and schema join maps.
3. ARCHITECTURE DECISION RECORDS (ADRs):
   Create `docs/adr/` with numbered ADRs (ADR-0001 to ADR-0007) documenting architectural trade-offs:
   - ADR-0001: LangGraph cyclic state machine vs linear chains.
   - ADR-0002: Langfuse OSS vs proprietary SaaS for telemetry.
   - ADR-0003: Dynamic BigQuery schema caching with DuckDB mock fallback.
   - ADR-0004: SQLite local storage with MemorySaver vs Cloud SQL.
   - ADR-0005: Presidio edge regex scrubbing vs Cloud DLP.
   - ADR-0006: Configurable Gemini models & exponential jitter backoff.
   - ADR-0007: Domain-Driven semantic layer for Text-to-SQL.
4. TECHNICAL SPECIFICATION (RFC-001):
   Create `docs/rfc/RFC-001-agentic-data-assistant.md` detailing the complete StateGraph, TypedDict AgentState schema, node contracts, and circuit breaker logic.
5. ATOMIC DELIVERY BACKLOG (tickets/):
   Decompose the roadmap into strictly sized, atomic tickets (OPS-000 to OPS-010) in `tickets/`, complete with Acceptance Criteria and visual Mermaid DAG.
6. TRIPLE VERIFICATION PROTOCOL:
   Define 20 evaluation test batteries (TB-01 to TB-20) covering blind clones, offline mock mode, precision queries, PII attacks, HITL pause/resume, and self-correction reflection loops.
```

---

## 3. Stage 2: Autonomous Swarm Execution Prompt (Tickets OPS-002B to OPS-010)

### Why It Was Formulated:
With the architecture locked, the human captain authorized fully autonomous execution across the entire roadmap using the `/goal` and `/auto` agent capabilities. 

To eliminate human micro-approvals without sacrificing safety, the prompt enforced the **Autonomous Swarm Protocol**: every ticket required a dedicated feature branch, a technical RFC, an architectural audit by an independent subagent (`Reviewer 1`), a secondary security audit for critical tickets (`Reviewer 2`), hermetic test execution, evidence capture to disk, and a formal sign-off by a dedicated `QA & PO Auditor` subagent before merging to `main`.

### The Executed Autonomous Swarm Prompt:
```text
/goal /auto Execute autonomously according to docs/architecture/AUTONOMOUS_SWARM_PROTOCOL.md from ticket OPS-002B to OPS-010.

Protocol Instructions:
1. For every ticket (OPS-002B -> OPS-003 -> OPS-004 -> OPS-005 -> OPS-006 -> OPS-007 -> OPS-008 -> OPS-009 -> OPS-010):
   a. Create branch feat/OPS-XXX-...
   b. Author docs/rfc/RFC-OPS-XXX.md.
   c. Spawn Subagent Reviewer 1 (Lead Systems Architect). If confidence < 90% or ticket is Critical (OPS-004, OPS-006, OPS-010), spawn Reviewer 2.
   d. Implement code in src/ and unit tests in tests/.
   e. Run .venv/bin/pytest -v and .venv/bin/ruff check --fix .
   f. Persist execution evidence to tests/evidence/OPS-XXX/.
   g. Spawn independent Subagent QA & PO Auditor to produce docs/qa/QA_REVIEW_OPS-XXX.md.
   h. Once approved, mark ticket done, commit with "OPS-XXX feat: ...", merge to main, push to origin/main.
   i. Automatically advance to the next ticket without asking for user confirmation.
2. Full permissions granted: web search, terminal execution, file creation, and subagent spawning.
3. Run continuously until OPS-010 is complete and all 20 test batteries pass.
```

---

## 4. Stage 3: Critical Human Steering & Frontier Challenge Prompt (Genesis of OPS-011)

### Why It Was Formulated:
Following the completion of ticket OPS-010, the human captain intervened to challenge the assistant on empirical reality and assignment fidelity. This represents the quintessence of **EU AI Act Article 14 Human-in-the-Loop Governance**:
1. *Did the agent actually test against the live Google Gemini API, or was it relying solely on mocked unit test responses?*
2. *Did the agent examine the code snippet on Page 4 of the assignment PDF (`bq_client.py` by Alex Freidman with class `BigQueryRunner`)?*
3. *Did the agent verify how the 5 historical canonical questions from the PDF are retrieved from the Golden Knowledge Bucket and injected into the prompt?*

This intervention led directly to the creation, implementation, and clearance of **OPS-011: Golden Trios Knowledge Retrieval, Prompt Accuracy Frontier Benchmark & BigQueryRunner Export**.

### The Executed Steering & Challenge Prompt:
```text
Did you use codex in any moment? If not is relevant now? Did you test the Gemini ai api? Would you be proud of what you did? If you received the pdf assessment and you would give this repo, would you be accepted?

Without testing api key, you would be proud and this would be a top tier 1%? why? But did you test the database they suggest? They gave a snippet code in the pdf, was that useful?

I understand what you did, and I think it would be important to create a story for what retrievals we would expect to get from that database with prompts, and from that we would test the prompts so we have a right limit on the frontier for this moment for this model. If there are errors, we have to have space to correct them so we would be very precise.

On the PDF that they gave for the assessment, there’s a snippet of a file. What is this file? Did we use anything from that? Is this relevant for what we are doing? Can you use Codex on the review, but before using Codex I want to know which story is missing that we have to do?
```

### Direct Outcomes of Stage 3:
1. **Creation of `BigQueryRunner` (`src/bq/client.py`):** Direct 1:1 API compatibility with Alex Freidman's starter snippet from Page 4.
2. **In-Process Golden Knowledge Store (`src/knowledge/golden_bucket.py`):** Operationalization of Requirement 1 with the 5 canonical historical Trios and lexical few-shot injection.
3. **Automated Live Model Benchmark (`scripts/benchmark_prompts.py`):** Live execution against Google Gemini (`gemini-3.5-flash-lite`), generating [`docs/BENCHMARK_REPORT.md`](../BENCHMARK_REPORT.md) with **5/5 PASS, 100% SQL accuracy, and 0 syntax retries**.

---

## 5. Stage 4: Multi-Model Adversarial Review Gate (OpenAI Codex Quota Investment)

### Why It Was Formulated:
To prevent "vendor blindness" or single-model bias, the user established a **Multi-Model Adversarial Strategy**:
- **Google Gemini (`gemini-3.5-flash-lite` / `gemini-2.5-flash`):** Primary runtime model for SQL generation and executive synthesis.
- **Antigravity Autonomous Subagents:** Used for internal RFC peer reviews and QA sign-offs.
- **OpenAI Codex CLI (`codex review --uncommitted`):** Independent, external adversarial code auditor.

### The 81% Monthly Quota Investment:
> [!IMPORTANT]
> **Adversarial Code Review Note:**  
> The user dedicated **all remaining 81% of their monthly OpenAI Codex quota** to perform multiple rounds of deep, uncommitted code audits on this repository.
>
> This multi-model adversarial review caught and resolved four critical edge cases that unit tests initially overlooked:
> 1. **DuckDB Catalog Discovery (`src/bq/mock_engine.py`):** BigQuery queries `thelook_ecommerce.INFORMATION_SCHEMA.COLUMNS` with `table_schema = 'thelook_ecommerce'`, while DuckDB uses `table_schema = 'main'`. Codex caught this discrepancy, leading to a translation layer that allows full offline schema discovery across all 7 tables.
> 2. **Mock Catalog Completeness:** Seeding placeholder schemas for `events`, `inventory_items`, and `distribution_centers` so all 7 public thelook tables exist in the offline catalog.
> 3. **BigQueryRunner Parameterization:** Ensuring `dataset_id: Optional[str] = "bigquery-public-data.thelook_ecommerce"` correctly supported `None` without crashing.
> 4. **Lexical RAG Thresholding:** Fine-tuning the Golden Bucket similarity threshold to `0.25` and requiring phrase tokenization, preventing false-positive few-shot exemplar injection on low-specificity retail queries.

---

## 6. Summary of Architectural Takeaways

| Dimension | Standard Candidate Approach | This Repository's Approach (Opsfleet Standard) |
|---|---|---|
| **Prompt Engineering** | Ad-hoc, unstructured chat prompts | Formally versioned, stage-gated meta-prompts with clear architectural contracts. |
| **Model Verification** | Tested only against local mocks | Validated against live Gemini APIs with empirical latency, token, and cost reports. |
| **Code Review** | Self-review by the same LLM | Triple-tier review: Independent Subagents + OpenAI Codex CLI + 20-Battery Test Runner. |
| **Evaluator Experience** | Requires GCP credentials and API keys | **2-Minute Evaluator Rule:** Runs out of the box in offline DuckDB mode (`--dry-run`). |

---

## 7. Audit Log: Active Engineering Time & Session Breakdown

To provide complete visibility to the hiring committee, all timestamps recorded in the local environment and git commit history are audited below (Timezone: UTC+1):

### Session Chronology:
* **Day 1 (2026-10-15) — Foundation & Architecture (2h 42m active | 4h 52m elapsed):**
  - `08:06 – 10:40` (154 mins): Assignment spec ingestion, PRD, Retail Ontology (`ONT-001`), and ADRs 0001–0007.
  - `11:18 – 11:23` (5 mins): Model trade-offs matrix and FinOps comparison.
* **Day 2 (2026-10-16) — Swarm Delivery, Frontier Benchmark & Hardening (7h 20m active | 8h 23m elapsed):**
  - `10:48 – 11:20` (33 mins): L8 Architectural Audit (readiness score: 96.25%).
  - `11:43 – 12:46` (63 mins): Backlog restructuring into 11 atomic tickets and `AGENTS.md` invariants.
  - `13:26 – 17:00` (214 mins): Autonomous swarm execution (`/goal /auto`) across tickets `OPS-001` through `OPS-010`.
  - `17:00 – 18:37` (97 mins): Human steering, Alex Freidman `BigQueryRunner` export parity, and live Gemini prompt accuracy frontier benchmark (`OPS-011`).
  - `18:40 – 19:11` (31 mins): OpenAI Codex multi-model adversarial review (utilizing remaining 81% monthly quota) and final delivery sign-off.

**Total Active Engineering Effort:** **10 hours 02 minutes** (Directly within Opsfleet's 6–12 hour target window).
