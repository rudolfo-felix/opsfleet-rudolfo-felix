## OPS-005: Saved Reports SQLite Storage & EU AI Act HITL Confirmation
Status: backlog  
Branch: feat/OPS-005-reports-hitl  
Priority: High  

### Overview
Implement the Saved Reports management library backed by local SQLite persistence, alongside a strict Human-In-The-Loop (HITL) interrupt gate before executing destructive operations (e.g., *"Delete all reports mentioning Client X"*).

### Goal
Fulfill EU AI Act Article 14 (Human Oversight) and Requirement 3 by ensuring the agent never purges saved reports without explicit, unambiguous human confirmation.

### Acceptance Criteria
1. Given an executive request to save an analysis (e.g. *"Save this as Q1 Retail Briefing"*), the report is stored with title, content, timestamp, and user tags in SQLite.
2. Given a request to delete reports (e.g. *"Delete all reports about California"*), the agent identifies the target reports, enters a paused state, and prompts the user (`Are you sure you want to delete X reports? [y/N]`).
3. If the user answers `N` or declines, deletion is aborted and reports remain intact.
4. If the user answers `y`, deletion executes and confirms the purged count.

### Implementation & Architecture
* 📄 **Related ADR:** [ADR-0004](../docs/adr/0004-sqlite-local-storage-vs-cloudsql.md)
* 📄 **Technical Spec:** [RFC-001](../docs/rfc/RFC-001-agentic-data-assistant.md)

### Completion Criteria
1. `src/storage/reports.py` implemented with CRUD operations.
2. LangGraph interrupt flow verified with both confirmation (`y`) and rejection (`N`) pathways.
