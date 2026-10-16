# RFC: OPS-010 - Production HLD Document, 20-Battery Test Runner & Delivery Gate

**Related Ticket:** [OPS-010](../../tickets/OPS-010-production-hld-and-20-battery-runner.md)  
**General Runbook:** [Autonomous Swarm Protocol](../architecture/AUTONOMOUS_SWARM_PROTOCOL.md)  
**Architectural Baseline:** [MASTER_PLAN.md](../MASTER_PLAN.md) §5, §9, [ASSIGNMENT_SPEC.md](../ASSIGNMENT_SPEC.md)

---

## 1. Technical Specification & Context

### 1.1 Problem Statement
Ticket OPS-010 represents the final delivery and quality gate of the Opsfleet Retail Data Analysis AI Assistant assessment. It produces the master deliverables evaluated by AI Tech Lead Vlad Bondarenko and Project Manager Harry:
1. **The Production High-Level Design (HLD) Document (`docs/HLD.md`):** Complete enterprise architecture specification addressing all 8 requirements of the assignment:
   - Req 1: Hybrid Intelligence & Golden Knowledge Bucket RAG ingestion/retrieval loop.
   - Req 2: Production Security, JWT claims, BigQuery Row-Level Security (RLS) & Dynamic Data Masking (DDM).
   - Req 3: High-Stakes Destructive Governance (Two-phase commit / EU AI Act Article 14).
   - Req 4: Continuous Learning Flywheel & Golden query promotion pipeline.
   - Req 5: Enterprise Resilience, GCP multi-region failover, and rate-limit backoff.
   - Req 6: Enterprise Quality Assurance Strategy (BIRD-SQL, Spider 2.0, LLM-as-a-judge).
   - Req 7: OpenTelemetry Observability & FinOps TCO Comparison (>85% savings vs commercial SaaS).
   - Req 8: Weekly Persona Agility via YAML/Prompt CMS without redeployments.
   - Deliverable 1: C4 Model Diagrams (Level 1 System Context, Level 2 Container, Level 3 Component in Mermaid).
2. **The Executive Showcase README (`README.md`):** Professional root guide satisfying the 2-Minute Evaluator Rule with quickstart, CLI options, architecture diagrams, and sample prompt recipes.
3. **The 20-Battery Test Runner (`scripts/verify_batteries.py`):** Programmatic verification harness executing all 20 evaluation batteries (TB-01 to TB-20) from `docs/MASTER_PLAN.md` §9.
4. **Markdown Link & Governance Auditor:** Automated script verifying 100% link resolution and commit linkage traceability across the repository.

---

## 2. Prerequisites & Invariants
- **Invariant 1 (2-Minute Clone-and-Run):** Root `README.md` gives copy-paste commands that execute in < 2 minutes on fresh environments.
- **Invariant 5 & Invariant 6 (Dual Engine & Sanitizer):** Documented in HLD and validated in test batteries.
- **Invariant 4 (FinOps Budget):** Validated in TB-17.
- **Invariant 10 (HITL Interrupt):** Validated in TB-12 and TB-13.
- **Invariant 12 (Evidence Gate):** Test results, coverage, and battery outputs stored in `tests/evidence/OPS-010/`.

---

## 3. Architecture & Execution Steps

### Step 1: Author Production High-Level Design (`docs/HLD.md`)
- Exhaustive engineering specification structured into 8 core requirement sections.
- Embedded Mermaid C4 diagrams:
  - C4 Level 1: System Context Diagram (Retail Executives, BigQuery, Google AI Studio/Vertex AI, Langfuse).
  - C4 Level 2: Container Diagram (GCP Cloud Run, BigQuery, Cloud SQL pgvector, Cloud Storage, OTel Collector).
  - C4 Level 3: Component Diagram (LangGraph StateGraph, Intent Classifier, SQL Generator, Execution Node, PII Sanitizer, Synthesizer, Checkpointer).
- Detailed FinOps TCO comparison table ($800–$3,000/mo commercial SaaS vs $50–$120/mo open-source GCP stack).

### Step 2: Deliver Production Root `README.md`
- Polish root `README.md` into the primary showcase for Vlad Bondarenko:
  - 2-Minute Quickstart (`git clone && pip install -e . && python main.py --dry-run`).
  - Architecture overview and ASCII/Mermaid flow.
  - Interactive CLI commands, flags (`--user-id`, `--brands`, `--mock-bq`).
  - Sample prompts across Sales, Churn, Margins, and Saved Reports.
  - Test suite commands and coverage badges.

### Step 3: Implement Automated 20-Battery Runner (`scripts/verify_batteries.py`)
- Python script executing TB-01 to TB-20:
  - TB-01 to TB-17: Executed via pytest harness, mock engine assertions, PII sanitization assertions, rate-limit backoff verification, and LangGraph interrupt verification.
  - TB-18 to TB-20: Automated file existence, Mermaid syntax parsing, markdown link resolution, and git commit history checks.
- Generates a styled terminal summary table and saves execution results.

### Step 4: Run Link Verification & Test Suite
- Run `verify_batteries.py`, `pytest -v`, and `ruff check .`.
- Persist evidence in `tests/evidence/OPS-010/`.
