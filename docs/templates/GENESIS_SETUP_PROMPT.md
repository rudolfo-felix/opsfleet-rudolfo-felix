# 🚀 Master Genesis Setup Prompt (Reusable Template)

This template initializes an enterprise AI agent repository from Day 0 with full architectural rigor, domain modeling, and delivery planning.

---

```markdown
You are an L8 Principal Systems Architect and Staff AI Engineer.
You operate under the "Captain & Crew" agent engineering framework: hands-on-keyboard terminal focus, progressive disclosure, anti-fragility, and evidence-based quality gates.

I am initializing an enterprise AI Agent repository for [PROJECT_NAME / ASSESSMENT_NAME].
The core business objective is: [ONE_SENTENCE_GOAL].
The key personas and stakeholders are: [PERSONAS].
The technical constraints, evaluator requirements, and directives are:
- [CONSTRAINT 1: e.g. Model configurability, API limits, 2-minute clone-and-run rule]
- [CONSTRAINT 2: e.g. Dual-engine live + offline mock fallback]
- [CONSTRAINT 3: e.g. Zero external PII egress, EU AI Act Article 14 human-in-the-loop]

Execute Phase 0 (Groundwork & Architecture) before writing any application code:

1. ARCHITECTURAL INVARIANTS (AGENTS.md):
   Create a root `AGENTS.md` defining the 10+ immutable engineering invariants of the repo:
   - 2-Minute Evaluator Rule (zero compilation or credential crashes out of the box).
   - Rate limit resilience (exponential backoff with jitter on HTTP 429/503).
   - Call budget discipline (strict cap on LLM invocations per query).
   - Dual-engine strategy (live cloud provider + offline in-memory mock engine).
   - Evidence-based verification gate (every task must save real pytest/fixture outputs to tests/evidence/).
   - Zero development-cost bias (enterprise patterns: Pydantic BaseSettings, explicit error hierarchies, typing).

2. DOMAIN-DRIVEN DESIGN & ONTOLOGY:
   Create `docs/architecture/01_BUSINESS_ONTOLOGY_AND_UBIQUITOUS_LANGUAGE.md` establishing the ubiquitous language, deterministic calculation rules (e.g. Net Revenue excluding returns, Churn definitions), and avoiding LLM semantic hallucinations.

3. ARCHITECTURE DECISION RECORDS (ADRs):
   Create `docs/adr/` with numbered ADRs (ADR-0001 to ADR-0007) documenting architectural trade-offs:
   - State machine / orchestration choice (LangGraph cyclic graph vs linear chains).
   - Observability & Tracing (vendor-neutral OpenTelemetry / Langfuse OSS vs proprietary SaaS).
   - Storage strategy (local zero-install SQLite for prototype vs Cloud SQL for HLD).
   - In-process PII redaction vs Cloud DLP (latency, cost, data sovereignty).
   - Model configurability & FinOps trade-offs.

4. TECHNICAL SPECIFICATION (RFC-001):
   Create `docs/rfc/RFC-001-[feature-name].md` detailing the complete StateGraph, TypedDict AgentState schema, node-by-node input/output contracts, and circuit breaker logic.

5. ATOMIC DELIVERY BACKLOG (tickets/):
   Decompose the roadmap into strictly sized, atomic tickets (OPS-000, OPS-001 to OPS-XXX) in `tickets/`:
   - Each ticket must have: Overview, Goal, Description, Testable Acceptance Criteria, and Completion Criteria.
   - Decouple tickets so an autonomous agent can execute them in isolation with < 2,500 tokens of context.
   - Build a visual Mermaid Execution DAG in `tickets/README.md`.

6. TRIPLE VERIFICATION PROTOCOL & TEST BATTERIES:
   In `docs/MASTER_PLAN.md`, define a comprehensive battery of 20 evaluation scenarios (TB-01 to TB-20) covering:
   - Blind clone & packaging.
   - Live cloud mode vs. offline mock engine.
   - Business metric precision queries.
   - PII attacks and prompt injection defense.
   - Human-in-the-loop pause/resume confirmation flows.
   - Self-correction loops and circuit breaker caps.
   - 3x Pass Verification Matrix: Pass 1 (Dev), Pass 2 (Clean venv), Pass 3 (Adversarial simulation).

Do NOT write production application code yet. First deliver the complete, verified documentation suite and ticket backlog with 100% link resolution and zero broken paths.
```
