## OPS-003: LangGraph State Schema & GoogleSQL Generation Node
Status: backlog  
Branch: feat/OPS-003-state-sql-gen  
Priority: Critical  

### Overview
Define the core `AgentState` schema using `typing.TypedDict` and implement the Text-to-SQL generation node using Google Gemini (`gemini-2.5-flash` via `google-genai`), guided by the Domain-Driven Design Retail Ontology (`ONT-001`) and few-shot exemplars.

### Goal
Translate natural language executive questions into high-precision, standard GoogleSQL queries respecting retail calculation rules and temporal functions.

### Description
- Implement `src/agent/state.py` defining `AgentState` (`user_query`, `allowed_brands`, `current_sql`, `sql_history`, `error_feedback`, `retry_count`, `query_results`, `total_llm_calls`, `tokens_consumed`).
- Implement `src/agent/prompts.py` embedding schema context, retail business formulas (Net Revenue strictly excluding `Cancelled` and `Returned`), GoogleSQL date functions (`TIMESTAMP_SUB`), and 3 exemplar Golden Bucket Trios.
- Implement `src/agent/nodes/generate_sql.py` invoking Gemini with the prompt, extracting clean SQL syntax, and populating `state["current_sql"]`.

### Acceptance Criteria
1. Given natural language queries (e.g. *"What is our Net Revenue by category?"*), the generator produces valid GoogleSQL without markdown ticks or formatting noise.
2. Generated SQL for revenue enforces `status NOT IN ('Cancelled', 'Returned')` per ONT-001.
3. Generated SQL for churn calculates trailing 90-day inactivity using BigQuery temporal syntax.
4. `total_llm_calls` is incremented accurately to enforce the 2–5 calls FinOps budget.

### Implementation & Architecture
- 📄 **Related ADR:** [ADR-0001](../docs/adr/0001-adopt-langgraph-state-machine.md) & [ADR-0007](../docs/adr/0007-domain-driven-semantic-layer-for-text-to-sql.md)
- 📄 **Technical Spec:** [RFC-001](../docs/rfc/RFC-001-agentic-data-assistant.md) §2.2, §3.2
- 🏛️ **Domain Ontology:** [01_BUSINESS_ONTOLOGY_AND_UBIQUITOUS_LANGUAGE.md](../docs/architecture/01_BUSINESS_ONTOLOGY_AND_UBIQUITOUS_LANGUAGE.md)

### Completion Criteria
1. `src/agent/state.py`, `src/agent/prompts.py`, and `src/agent/nodes/generate_sql.py` implemented.
2. Verified with unit tests in `tests/test_sql_generation.py`.
