# RFC: OPS-007 - Saved Reports SQLite Storage & EU AI Act HITL Interrupt

**Related Ticket:** [OPS-007](../../tickets/OPS-007-saved-reports-and-hitl-interrupt.md)  
**General Runbook:** [Autonomous Swarm Protocol](../architecture/AUTONOMOUS_SWARM_PROTOCOL.md)
**Architectural References:** [ADR-0004](../adr/0004-sqlite-local-storage-vs-cloudsql.md), Invariant 1 (2-Minute Rule), Invariant 10 (HITL Interrupt & MemorySaver Checkpointer), Mitigation 5 (MemorySaver Thread Tracking), [PRD-RETAIL-ASSISTANT.md](../prd/PRD-RETAIL-ASSISTANT.md) (FR-4)

---

## 1. Executive Summary & Problem Statement

This RFC specifies the architecture and implementation for persistent local report storage and human-in-the-loop governance:
1. **Persistent Local Report Storage (`src/storage/reports.py`):** Operates on local SQLite (`reports.db`), storing executive briefings and synthesized insights with CRUD functionality and case-insensitive keyword filtering.
   - Per **ADR-0004** and the **2-Minute Evaluator Rule (Invariant 1)**, this uses standard-library `sqlite3`, requiring zero external database setup, cloud billing, or network provisioning.
2. **EU AI Act Article 14 Human Oversight Gate (`src/agent/nodes/reports.py`):** Implements Human-In-The-Loop (HITL) interrupt patterns for high-stakes, destructive operations (e.g. deleting saved reports).
   - In accordance with EU AI Act Article 14 (Human Oversight), autonomous agents must not execute irreversible destructive actions without explicit, auditable human authorization.
   - LangGraph's native `interrupt()` pauses graph execution, persisting execution state into `MemorySaver`.
   - When resumed with `Command(resume='yes')` or `Command(resume='no')`, the node commits or aborts the operation safely.
3. **Graph Assembly & MemorySaver Integration (`src/agent/graph.py`):** Wires the reports management node into the LangGraph state machine with full session thread isolation (`thread_id`).

---

## 2. Technical Specification & Design

### 2.1 SQLite Schema & CRUD Interface (`src/storage/reports.py`)

#### Database Schema:
```sql
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tags TEXT
);

CREATE INDEX IF NOT EXISTS idx_reports_user_id ON reports(user_id);
CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports(created_at);
```

#### Core APIs:
- `init_db(db_path: str | Path | None = None) -> None`: Ensures tables and indexes are initialized.
- `save_report(user_id: str, title: str, content: str, tags: list[str] | str | None = None, db_path: str | Path | None = None) -> int`: Persists a briefing and returns its autoincrement ID.
- `list_reports(user_id: str | None = None, keyword: str | None = None, db_path: str | Path | None = None) -> list[dict[str, Any]]`: Retrieves reports matching user and optional case-insensitive keyword across title or content.
- `get_report(report_id: int, db_path: str | Path | None = None) -> dict[str, Any] | None`: Fetches a single report by ID.
- `delete_report(report_id: int, db_path: str | Path | None = None) -> bool`: Deletes report by ID; returns `True` if found and deleted, `False` otherwise.

---

### 2.2 LangGraph HITL Interrupt Node (`src/agent/nodes/reports.py`)

#### State & Node Operations:
1. **List Reports:** Triggered by `"list reports"`, `"show saved reports"`, etc. Formats results into a clean markdown table.
2. **Save Report:** Triggered by `"save report <title>"`. Saves `state["executive_report"]` into `reports.db`.
3. **Destructive Deletion:** Triggered by `"delete report #X"`.
   - Extracts target `report_id`.
   - Pauses execution via `interrupt()`:
     ```python
     confirmation = interrupt({
         "action": "delete_report",
         "report_id": report_id,
         "prompt": f"⚠️ EU AI Act Article 14 Oversight: Are you sure you want to delete report #{report_id}? [y/N]: ",
     })
     ```
   - On resumption:
     - If user input in `('y', 'yes', 'true', '1')`: calls `delete_report(report_id)` and returns confirmation.
     - Else: returns abort notice without modifying the database.

---

### 2.3 Mitigation 5: MemorySaver Checkpointer State Isolation

- Every run in the CLI or automated runner specifies a unique thread ID:
  ```python
  config = {"configurable": {"thread_id": session_id}}
  ```
- When `interrupt()` fires, `MemorySaver` snapshots the entire state to memory.
- Invoking the compiled graph with `Command(resume=user_response)` resumes directly inside `reports_node`, fulfilling Invariant 10 and Mitigation 5.

---

## 3. Execution Steps

1. **Step 1: Module `src/storage/reports.py`:**
   - Implement `init_db`, `save_report`, `list_reports`, `get_report`, `delete_report`.
2. **Step 2: Module `src/agent/nodes/reports.py`:**
   - Implement `reports_node` with `interrupt()` and CRUD routing.
3. **Step 3: Update `src/agent/graph.py`:**
   - Replace stub with `src.agent.nodes.reports.reports_node`.
   - Update `route_intent` for save/list/delete commands.
4. **Step 4: Unit Test Suite (`tests/test_destructive_ops.py`):**
   - Test CRUD and keyword search on temp SQLite database.
   - Test `interrupt()` pause with `MemorySaver`.
   - Test resumption with confirmation (`yes` $\rightarrow$ deleted).
   - Test resumption with denial (`no` $\rightarrow$ aborted, record intact).
5. **Step 5: Evidence & Subagent Review:**
   - Persist evidence in `tests/evidence/OPS-007/`.
   - Lead QA & PO Auditor sign-off.
