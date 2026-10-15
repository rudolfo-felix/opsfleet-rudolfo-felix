# Delivery Tickets & Sprints Index

This directory contains the user stories, acceptance criteria, and completion criteria for each atomic milestone of the **Retail Data Analysis AI Assistant**.
Every commit and feature branch maps directly to a ticket ID (`OPS-XXX`).

---

## 📋 Active Tickets Table

| Story ID | Title | Status | Branch | PR | Priority |
|:---:|---|:---:|:---:|:---:|:---:|
| **[OPS-001](./OPS-001-environment-scaffolding.md)** | Repository Scaffolding, Pinned Dependencies & Config | `backlog` | `feat/OPS-001-scaffolding` | - | High |
| **[OPS-002](./OPS-002-bigquery-schema-client.md)** | BigQuery Client, Dynamic Schema Caching & Mock Engine | `backlog` | `feat/OPS-002-bigquery-client` | - | High |
| **[OPS-003](./OPS-003-langgraph-self-correction.md)** | LangGraph Agent Brain, GoogleSQL Gen & Self-Correction Loop | `backlog` | `feat/OPS-003-langgraph-core` | - | Critical |
| **[OPS-004](./OPS-004-pii-masking-guardrails.md)** | Enterprise PII Redaction & User Brand Scoping Guardrails | `backlog` | `feat/OPS-004-pii-guardrails` | - | Critical |
| **[OPS-005](./OPS-005-saved-reports-hitl.md)** | Saved Reports SQLite Storage & EU AI Act HITL Confirmation | `backlog` | `feat/OPS-005-reports-hitl` | - | High |
| **[OPS-006](./OPS-006-rich-cli-observability.md)** | Rich Interactive CLI Interface & OTel-Compliant Telemetry | `backlog` | `feat/OPS-006-cli-telemetry` | - | High |
| **[OPS-007](./OPS-007-production-hld.md)** | C4 Model High-Level Design (HLD) Document (8 Requirements) | `backlog` | `feat/OPS-007-hld-docs` | - | Critical |

---

## 🛠️ Commit Message Rule
Every commit message must be linked to its corresponding story ID:
```text
OPS-XXX <type>(<scope>): <summary in imperative mood>
```
*Example:* `OPS-001 feat(env): configure requirements.txt and pydantic settings`
