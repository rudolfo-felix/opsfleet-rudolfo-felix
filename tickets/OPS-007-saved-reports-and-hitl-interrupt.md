## OPS-007: Saved Reports SQLite Storage & EU AI Act HITL Interrupt
Status: backlog  
Branch: feat/OPS-007-reports-hitl  
Priority: High  

### Overview
Implement persistent local SQLite storage for saved reports (`reports.db`) and configure LangGraph Human-In-The-Loop (HITL) interrupt patterns (`interrupt()`) paired with `MemorySaver` checkpointer for destructive operations (e.g. deleting saved reports).

### Goal
Provide report persistence for executive workflows and enforce human governance over destructive operations in strict compliance with EU AI Act Article 14 (Human Oversight).

### Description
- Implement `src/storage/reports.py` managing SQLite schema (`reports` table: id, user_id, title, content, created_at, tags).
- Implement CRUD operations: `save_report()`, `list_reports()`, `delete_report()`.
- Implement `src/agent/nodes/reports.py` integrating LangGraph `interrupt()`: any command to delete reports halts graph execution and prompts the user for explicit confirmation (`Are you sure you want to delete report #X? [y/N]`).
- Configure graph with `MemorySaver` checkpointer and thread session tracking to enable clean resumption on confirmation (Mitigation 5).

### Acceptance Criteria
1. Executives can save synthesized briefings to SQLite and list them by keyword or user ID.
2. Destructive delete commands trigger a paused graph state (`interrupt`), requesting user input.
3. If user confirms with `y` or `yes`, deletion commits and confirms.
4. If user cancels with `n` or anything other than confirmation, deletion aborts and data remains intact.

### Implementation & Architecture
- 📄 **Related ADR:** [ADR-0004](../docs/adr/0004-sqlite-local-storage-vs-cloudsql.md)
- 📄 **Technical Spec:** [RFC-001](../docs/rfc/RFC-001-agentic-data-assistant.md) §3.5
- 📄 **PRD Requirements:** [PRD-RETAIL-ASSISTANT.md](../docs/prd/PRD-RETAIL-ASSISTANT.md) (FR-4)

### Completion Criteria
1. `src/storage/reports.py` and `src/agent/nodes/reports.py` implemented.
2. Verified with unit tests in `tests/test_destructive_ops.py`.
