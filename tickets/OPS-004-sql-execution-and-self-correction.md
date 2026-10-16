## OPS-004: Execution Node, Self-Correction Loop & FinOps Circuit Breaker
Status: backlog  
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
- Implement `src/agent/graph.py` assembling the LangGraph StateGraph with conditional edges routing errors to `self_correct` and capping at `retry_count <= 2`.

### Acceptance Criteria
1. Given a SQL compiler error (e.g. invalid syntax or column name), the agent routes to `self_correct`, reinjecting the exact compiler error message.
2. Given a query returning 0 rows, the agent diagnoses potential filter or casing issues and attempts correction if `retry_count < 2`.
3. Given 2 consecutive failed attempts, the circuit breaker triggers, halts execution gracefully, and informs the user without throwing raw tracebacks.
4. Successful queries transition to the downstream sanitization/synthesis pipeline.

### Implementation & Architecture
- 📄 **Related ADR:** [ADR-0001](../docs/adr/0001-adopt-langgraph-state-machine.md)
- 📄 **Technical Spec:** [RFC-001](../docs/rfc/RFC-001-agentic-data-assistant.md) §2.1, §3.3

### Completion Criteria
1. `src/agent/nodes/execute_sql.py`, `src/agent/nodes/self_correct.py`, and `src/agent/graph.py` implemented.
2. Verified with unit tests in `tests/test_self_correction.py` simulating compiler errors, empty results, and the circuit breaker.
