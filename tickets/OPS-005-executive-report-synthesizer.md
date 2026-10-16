## OPS-005: Executive Insight & Action Item Synthesizer Node
Status: done  
Branch: feat/OPS-005-report-synthesizer  
Priority: High  

### Overview
Implement the executive reporting synthesis node in LangGraph (`src/agent/nodes/synthesize.py`), transforming raw BigQuery tabular DataFrames into strategic markdown briefings tailored to Sarah (CEO / VP of Retail) with executive summaries, numeric highlights, and actionable Q2 recommendations.

### Goal
Elevate the assistant from a simple SQL runner to an executive decision-support partner, satisfying PRD FR-6.

### Description
- Implement `src/agent/nodes/synthesize.py` invoking Gemini with sanitized query data and the original user intent.
- **Privacy Enforcement Gate (GDPR / FR-2):** Synthesizer strictly consumes `state["sanitized_results"]` (scrubbed of customer names, emails, and IP addresses by `src/guardrails/pii.py`), NEVER raw `query_results`, guaranteeing zero PII leaks into the LLM context.
- Structure synthesis prompt to generate a 3-part markdown briefing:
  1. `## Executive Summary` (macro business takeaway for Sarah).
  2. `## Key Findings` (clean markdown tables or formatted metrics).
  3. `## Q2 Action Items` (concrete strategic decisions).
- Store final formatted report in `state["executive_report"]` and increment `state["total_llm_calls"]` by 1.

### Acceptance Criteria
1. Given tabular results, the synthesizer consumes `sanitized_results` rather than raw data, preventing PII transmission to the LLM.
2. The output report strictly includes three H2 markdown sections: `## Executive Summary`, `## Key Findings`, and `## Q2 Action Items`.
3. Reports include concrete business insights aligned with Retail Domain Ontology metrics (Net Revenue, Gross Margin, Churn).
4. `total_llm_calls` is incremented by exactly 1 during synthesis.
5. The synthesizer gracefully formats empty or single-row aggregations with executive context.

### Implementation & Architecture
- 📄 **Related PRD:** [PRD-RETAIL-ASSISTANT.md](../docs/prd/PRD-RETAIL-ASSISTANT.md) §3 (FR-2, FR-6)
- 📄 **Technical Spec:** [RFC-001](../docs/rfc/RFC-001-agentic-data-assistant.md) §2.1, §3.4
- 📄 **Security Gate:** [OPS-006](./OPS-006-enterprise-pii-and-brand-scoping.md)

### Completion Criteria
1. `src/agent/nodes/synthesize.py` implemented with PII-safe inputs and structured sections.
2. Verified with unit tests in `tests/test_synthesis.py`.
