# Master Documentation Index

Welcome to the technical documentation repository for the **Retail Data Analysis AI Assistant**.  
This documentation suite follows enterprise architecture standards (C4 Model, MADR, RFC, and PRD) designed for both executive stakeholders and technical evaluators.

---

## 🗺️ Documentation Map & Recommended Reading Order

```text
1. Business Context & Requirements:
   └── docs/prd/PRD-RETAIL-ASSISTANT.md    ──> Product Requirements & Executive Personas
   └── docs/ASSIGNMENT_SPEC.md              ──> Original Opsfleet Challenge Specification
   └── docs/JOB_DESCRIPTION.md              ──> Opsfleet AI Engineer Role Specification

2. Operational Strategy & Alignment:
   └── docs/MASTER_PLAN.md                  ──> Master Plan, Slack Q&A with Harry & Vlad, FinOps

3. Engineering Design & Proposed Solution:
   └── docs/rfc/RFC-001-agentic-data-assistant.md ──> Technical Specification & StateGraph Design
   └── docs/architecture/01_BUSINESS_ONTOLOGY_AND_UBIQUITOUS_LANGUAGE.md ──> Retail DDD & Master Acronyms

4. Immutable Architecture Decisions (ADRs):
   └── docs/adr/README.md                   ──> ADR Index Table
       ├── 0001-adopt-langgraph-state-machine.md
       ├── 0002-adopt-langfuse-oss-for-observability.md
       ├── 0003-bigquery-dynamic-schema-with-mock-fallback.md
       ├── 0004-sqlite-local-storage-vs-cloudsql.md
       ├── 0005-presidio-pii-masking-vs-cloud-dlp.md
       ├── 0006-configurable-gemini-flash-and-rate-limit-backoff.md
       └── 0007-domain-driven-semantic-layer-for-text-to-sql.md

5. Enterprise High-Level Design (Production Blueprint):
   └── docs/HLD.md                          ──> C4 Model (L1 Context, L2 Container, L3 Component)

6. Delivery Management & Sprints:
   └── tickets/README.md                    ──> Kanban Ticket Index (OPS-000 through OPS-010)
```

---

## 📂 Documentation Directory Reference

| Directory / File | Description | Target Audience |
|---|---|---|
| **[`prd/`](./prd/PRD-RETAIL-ASSISTANT.md)** | Product Requirements Document outlining executive personas, business problem, and functional requirements. | Product Managers, C-Level, Evaluators |
| **[`rfc/`](./rfc/RFC-001-agentic-data-assistant.md)** | Request for Comments (RFC-001) specifying technical implementation, LangGraph state machine, and error handling. | AI Engineers, Software Architects |
| **[`architecture/`](./architecture/01_BUSINESS_ONTOLOGY_AND_UBIQUITOUS_LANGUAGE.md)** | Domain-Driven Design (DDD) Business Ontology, Ubiquitous Language, and Master Acronyms. | Enterprise Architects, Data Engineers |
| **[`adr/`](./adr/README.md)** | Architecture Decision Records (MADR standard) documenting irreversible technical choices and trade-offs. | Technical Leads, Staff Architects |
| **[`MASTER_PLAN.md`](./MASTER_PLAN.md)** | Complete operational master plan, Slack transcripts, regulatory compliance, and FinOps comparison. | Hiring Committee, Project Managers |
| **[`assets/`](./assets/)** | Original client PDFs, role specifications, and the LangChain enterprise whitepaper. | Archival & Compliance Reference |

---

## 📦 Assets & Reference Whitepapers
* 📑 [AI Technical Assignment - Retail Company.pdf](./assets/AI%20Technical%20Assignment%20-%20Retail%20Company.pdf)
* 📑 [AI Engineer Opsfleet.pdf](./assets/AI%20Engineer%20Opsfleet.pdf)
* 📚 [The Agentic Operating Model.pdf](./assets/The%20Agentic%20Operating%20Model.pdf) — Enterprise blueprint for the Agent Development Lifecycle (ADLC).
