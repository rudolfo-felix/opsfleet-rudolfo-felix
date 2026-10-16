# RFC: OPS-005 - Executive Insight & Action Item Synthesizer Node

**Related Ticket:** [OPS-005](../../tickets/OPS-005-executive-report-synthesizer.md)  
**General Runbook:** [Autonomous Swarm Protocol](../architecture/AUTONOMOUS_SWARM_PROTOCOL.md)
**Architectural References:** [PRD-RETAIL-ASSISTANT.md](../prd/PRD-RETAIL-ASSISTANT.md) (FR-2, FR-6), [RFC-001](../rfc/RFC-001-agentic-data-assistant.md) §3.4, Invariant 4 (FinOps 2-5 Call Budget)

---

## 1. Executive Summary & Problem Statement

This RFC specifies the technical design for the **Executive Insight & Action Item Synthesizer Node** (`src/agent/nodes/synthesize.py`).

Traditional data assistants simply dump raw SQL tables or JSON records into the chat. For retail executives like Sarah (CEO / VP of Retail), raw data creates cognitive overload and fails to provide actionable strategic guidance.
The synthesizer node transforms sanitized tabular query results and the executive's original intent into a professional, high-impact strategic briefing structured strictly into three H2 sections:
1. `## Executive Summary` (High-level commercial takeaway).
2. `## Key Findings` (Formatted metrics, trends, and table highlights).
3. `## Q2 Action Items` (Concrete operational decisions and next steps).

Crucially, to satisfy GDPR and Invariant 9 (Privacy Gate / FR-2), the synthesizer strictly accesses `state["sanitized_results"]`, guaranteeing zero PII attributes (`email`, `first_name`, `last_name`, `ip_address`) reach the LLM context.

---

## 2. Technical Specification & Design

### 2.1 Synthesis Pipeline Architecture

```
         +--------------------------------------------------+
         |                 AgentState                       |
         |  - user_query: "What is our Net Revenue by cat?" |
         |  - sanitized_results: [{"category": "Jeans",..}] |
         |  - current_sql: "SELECT category, SUM(...)..."   |
         +--------------------------------------------------+
                                  |
                                  v
         +--------------------------------------------------+
         |       src/agent/nodes/synthesize.py              |
         |  - Validates sanitized_results input             |
         |  - Builds executive synthesis prompt             |
         |  - Invokes Gemini (model_name via google-genai)  |
         |  - Enforces 3 H2 Markdown Sections               |
         +--------------------------------------------------+
                                  |
                                  v
         +--------------------------------------------------+
         |                 State Update                     |
         |  - executive_report: "## Executive Summary..."   |
         |  - total_llm_calls += 1                          |
         |  - tokens_consumed += usage.total_tokens         |
         +--------------------------------------------------+
```

### 2.2 Privacy & PII Boundary Enforcement

- The synthesizer strictly prioritizes `state.get("sanitized_results")`.
- If `sanitized_results` is not yet populated (e.g. in tests before OPS-006 pipeline integration), an in-node defensive scrubber ensures any residual PII keys (`email`, `first_name`, `last_name`, `street_address`, `ip_address`) are masked (`***MASKED***`) before passing data to the LLM prompt.
- This ensures 100% compliance with GDPR Article 5 and EU data minimization principles.

### 2.3 Synthesis Prompt Design

The system instruction sets the persona of a Senior Retail Analytics Strategy Director briefing the CEO:
- **Tone:** Concise, strategic, data-grounded, avoiding fluff.
- **Section 1: `## Executive Summary`:** 2–3 sentences highlighting the macroeconomic trend, primary revenue driver, or strategic risk.
- **Section 2: `## Key Findings`:** Clean Markdown table or bullet points displaying exact numeric metrics (dollars, percentages, units).
- **Section 3: `## Q2 Action Items`:** 2–3 concrete, actionable initiatives (e.g. inventory rebalancing, pricing adjustments, retention campaigns).
- **Graceful Fallbacks:** If the dataset is empty (`[]`), the synthesizer explains the empty state in Sarah's language without technical jargon.

### 2.4 FinOps Call Accounting

- Invocations are wrapped with `@retry_with_backoff` from `src.agent.resilience`.
- Increments `state["total_llm_calls"]` by exactly 1.
- Tracks `tokens_consumed` from `usage_metadata.total_token_count`.

---

## 3. Execution Steps

1. **Step 1: Implement `src/agent/nodes/synthesize.py`:**
   - Define prompt builder, defensive PII scrubber, and node execution function.
2. **Step 2: Update `src/agent/graph.py`:**
   - Connect the real `synthesize` node to replace the previous stub.
3. **Step 3: Unit Tests in `tests/test_synthesis.py`:**
   - Verify 3 H2 sections exist in the generated report.
   - Verify `sanitized_results` consumption and PII scrubbing.
   - Verify `total_llm_calls` increments by exactly 1.
   - Verify empty-state formatting.
4. **Step 4: Evidence & Review:**
   - Persist evidence in `tests/evidence/OPS-005/`.
   - Lead Systems Architect subagent review.
   - QA & PO Auditor subagent sign-off.
