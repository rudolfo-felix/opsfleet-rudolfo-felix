## OPS-003: LangGraph Agent Brain, GoogleSQL Gen & Self-Correction Loop
Status: backlog  
Branch: feat/OPS-003-langgraph-core  
Priority: Critical  

### Overview
Implement the core LangGraph `StateGraph` state machine that handles natural language intent routing, GoogleSQL generation with dynamic schema injection, query execution, and an autonomous self-correction loop when errors occur.

### Goal
Provide robust natural language to BigQuery data analysis, capable of recovering from SQL errors within a capped retry budget ($\le 2$ retries).

### Acceptance Criteria
1. Given a business question (e.g. *"What are the top 5 selling product categories by revenue in 2023?"*), the agent generates valid BigQuery GoogleSQL and executes it.
2. Given a query that causes a syntax error or references an invalid column, the agent catches the error, transitions to the `self_correct` node, and attempts an auto-fix.
3. Given repeated errors, the self-correction loop halts after 2 retries, returning a polite executive explanation rather than crashing.
4. Total LLM calls per query remain within 2–5 to protect Google AI Studio rate limits.

### Implementation & Architecture
* 📄 **Related ADR:** [ADR-0001](../docs/adr/0001-adopt-langgraph-state-machine.md)
* 📄 **Technical Spec:** [RFC-001](../docs/rfc/RFC-001-agentic-data-assistant.md)

### Completion Criteria
1. `src/agent/state.py`, `src/agent/graph.py`, and `src/agent/prompts.py` implemented.
2. Self-correction loop verified with an intentionally faulty SQL test case.
