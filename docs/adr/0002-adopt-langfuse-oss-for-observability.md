# ADR-0002: Adopt Langfuse OSS over LangSmith for Enterprise Telemetry

* **Status:** Accepted
* **Date:** 2026-10-15
* **Deciders:** Rudolfo Félix (AI Engineer)
* **Technical Story:** [RFC-001](../rfc/RFC-001-agentic-data-assistant.md)

---

## Context & Problem Statement
Requirement 7 demands enterprise observability, tracking token consumption, latency, and trajectory debugging. While LangChain's *The Agentic Operating Model* whitepaper highlights LangSmith, enterprise retail clients face severe commercial and regulatory constraints:
1. **Cost Escalation:** LangSmith costs $39/seat/month plus $2.50 to $5.00 per 1,000 traces above strict limits.
2. **Data Sovereignty & GDPR:** Sending raw enterprise retail queries and database outputs to an external commercial SaaS (hosted in third-party US infrastructure) violates data minimization and GDPR compliance.
3. **Open Standards:** The industry is standardizing on CNCF **OpenTelemetry (OTel)** GenAI semantic conventions rather than proprietary APM wrappers.

## Considered Options
1. **Langfuse OSS (Selected for HLD & Production):** 100% Open-Source (MIT License), self-hostable in GCP VPC via Docker/Kubernetes for $0 software license cost.
2. **LangSmith:** Commercial proprietary SaaS, seat-based paywall, expensive self-hosted enterprise tier (> $10k/yr).
3. **Arize Phoenix:** Strong open-source tracing and evals, but less mature prompt management CMS.
4. **Datadog APM:** Enterprise standard for traditional microservices, but lacks GenAI-native evaluation scorecards and prompt versioning.

## Decision Outcome
Adopt **Langfuse OSS (Self-Hosted on Google Cloud Run + PostgreSQL)** for the production High-Level Design (HLD), and use OpenTelemetry-compatible local logging in the prototype.

### Positive Consequences
* **Zero Software Licensing Overhead:** Saves the retail client ~$800 to $3,000/month compared to commercial SaaS.
* **Strict GDPR & EU AI Act Compliance:** 100% of telemetry traces, database rows, and executive questions remain strictly within the client's private Google Cloud VPC.
* **Integrated Prompt CMS:** Free versioning and labeling for persona management (answering Requirement 8).
* **Native OpenTelemetry:** Emits traces conforming to the official CNCF `gen_ai.*` namespace.

### Negative / Neutral Consequences
* Self-hosting requires maintaining a PostgreSQL/ClickHouse database and Cloud Run instance (estimated cloud compute: ~$15–$30/month).
