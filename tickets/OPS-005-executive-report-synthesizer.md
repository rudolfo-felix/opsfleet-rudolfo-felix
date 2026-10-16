## OPS-005: Executive Insight & Action Item Synthesizer Node
Status: backlog  
Branch: feat/OPS-005-report-synthesizer  
Priority: High  

### Overview
Implement the executive reporting synthesis node in LangGraph (`src/agent/nodes/synthesize.py`), transforming raw BigQuery tabular DataFrames into strategic markdown briefings tailored to Sarah (CEO / VP of Retail) with executive summaries, numeric highlights, and actionable Q2 recommendations.

### Goal
Elevate the assistant from a simple SQL runner to an executive decision-support partner, satisfying PRD FR-6.

### Description
- Implement `src/agent/nodes/synthesize.py` invoking Gemini with query results and the original user intent.
- Structure synthesis prompt to demand:
  1. Executive Summary (macro business takeaway).
  2. Key Numeric Findings (clean markdown tables or formatted metrics).
  3. Strategic Next Steps / Q2 Action Items (concrete business decisions).
- Store final formatted report in `state["executive_report"]`.

### Acceptance Criteria
1. Given tabular results from BigQuery or Mock DuckDB, the output is formatted as a polished markdown briefing rather than a raw dictionary/table dump.
2. Reports include concrete business insights aligned with Retail Domain Ontology metrics (Net Revenue, Gross Margin, Churn).
3. The synthesizer gracefully formats empty or single-row aggregations with executive context.

### Implementation & Architecture
- 📄 **Related PRD:** [PRD-RETAIL-ASSISTANT.md](../docs/prd/PRD-RETAIL-ASSISTANT.md) §3 (FR-6)
- 📄 **Technical Spec:** [RFC-001](../docs/rfc/RFC-001-agentic-data-assistant.md) §2.1

### Completion Criteria
1. `src/agent/nodes/synthesize.py` implemented.
2. Verified with unit tests in `tests/test_synthesis.py`.
