# ADR-0004: Local SQLite Persistence vs. Cloud SQL for Saved Reports

* **Status:** Accepted
* **Date:** 2026-10-15
* **Deciders:** Rudolfo Félix (AI Engineer), Harry (Opsfleet PM Alignment)
* **Technical Story:** [RFC-001](../rfc/RFC-001-agentic-data-assistant.md)

---

## Context & Problem Statement
Requirement 3 mandates managing a "Saved Reports" library and enforcing a confirmation flow before executing destructive operations (e.g., *"Delete all reports mentioning Client X"*).
We must decide on the persistence backend for saved reports, balancing prototype portability against production scalability.

## Decision Drivers
* Prototype simplicity: Zero external daemon setup for the reviewer.
* Explicit approval from Harry (Opsfleet AI PM) in the Slack alignment: *"Yes, a local SQLite file or in-memory/JSON store is completely sufficient for the prototype. Cover the intended production persistence approach in your technical explanation."*
* Production readiness: High availability and concurrent access in production.

## Considered Options
1. **Local SQLite (`reports.db`) for Prototype + Cloud SQL (PostgreSQL) in HLD (Selected):** Zero-install, file-based persistence for local execution; fully specified Cloud SQL with automated backups in production architecture.
2. **Local PostgreSQL via Docker Compose for Prototype:** Enterprise-like, but violates the 2-minute setup rule by requiring Docker daemon and network port configuration.
3. **In-Memory Dictionary Only:** Discards saved reports on CLI exit; poor UX for demonstrating report persistence across sessions.

## Decision Outcome
Use **local SQLite (`sqlite3`)** in `src/storage/reports.py` for the CLI prototype, and document **Google Cloud SQL for PostgreSQL** in the production HLD (`docs/HLD.md`).

### Positive Consequences
* Works out of the box on any Python 3.10+ runtime without installing database servers or running Docker containers.
* Saved reports persist across CLI restarts in a local `.sqlite` file.
* Strict architectural alignment with Opsfleet's official PM guidance.

### Negative / Neutral Consequences
* Local SQLite does not support distributed multi-user concurrency (addressed in production HLD via Cloud SQL).
