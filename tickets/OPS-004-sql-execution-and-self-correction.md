## OPS-004: Execution Node, Self-Correction Loop & FinOps Circuit Breaker
Status: done  
Branch: feat/OPS-004-execution-self-correction  
Priority: Critical  

### Overview
Implement the SQL query execution node, the cyclical error reflection/self-correction node in LangGraph, and a deterministic circuit breaker capping retries at $\le 2$ attempts. Handle both hard compiler errors and empty result (0 rows) feedback.

### Goal
Provide autonomous query healing without user intervention while guaranteeing zero infinite loops and strict compliance with Google AI Studio free tier limits.

### Description
- Implement `src/agent/nodes/execute_sql.py` executing `state["current_sql"]` via `DualBigQueryClient`.
- Implement `src/agent/nodes/self_correct.py` analyzing compiler errors or empty result states, formulating precise corrective feedback, and re-invoking the model to produce revised SQL.
- Handle empty results (0 rows): if a query returns 0 rows due to case-sensitivity (e.g. `'complete'` vs `'Complete'`) or restrictive date filters, provide constructive feedback to self-correct (Mitigation 3).
- Implement `src/agent/graph.py` assembling the LangGraph StateGraph:
  - Add Intent Classifier conditional routing at entrypoint: routes analytical data questions to `generate_sql`, report deletion commands to `reports_node` (OPS-007 HITL), and general questions to a help summary.
  - Add conditional execution edge: routes compiler/runtime errors and 0-rows feedback to `self_correct` if `retry_count < 2`.
  - Cap retries deterministically: when `retry_count == 2`, trigger circuit breaker immediately without further LLM calls.
  - Provide minimal pass-through node stubs for `synthesize` (OPS-005) and `reports` (OPS-007) so the StateGraph compiles and unit tests run cleanly before downstream tickets are implemented.

### Acceptance Criteria
1. Given a user input, `graph.py` routes analytical queries to `generate_sql` and report deletion intents to the HITL reports node.
2. Given a SQL compiler error (e.g. invalid syntax or column name), the agent routes to `self_correct`, reinjecting the exact compiler error message.
3. Given a query returning 0 rows, the agent diagnoses potential filter or casing issues and attempts correction if `retry_count < 2`.
4. When `retry_count == 2`, the circuit breaker halts execution gracefully and informs the user without throwing raw tracebacks.
5. Successful queries transition to the downstream sanitization/synthesis pipeline.

### Implementation & Architecture
- 📄 **Related ADR:** [ADR-0001](../docs/adr/0001-adopt-langgraph-state-machine.md)
- 📄 **Technical Spec:** [RFC-001](../docs/rfc/RFC-001-agentic-data-assistant.md) §2.1, §3.3

### Completion Criteria
1. `src/agent/nodes/execute_sql.py`, `src/agent/nodes/self_correct.py`, and `src/agent/graph.py` (with intent routing) implemented.
2. Verified with unit tests in `tests/test_self_correction.py` simulating compiler errors, empty results, and the circuit breaker.
