# ADR-0005: Deterministic Presidio PII Masking vs. Google Cloud Sensitive Data Protection (DLP)

* **Status:** Accepted
* **Date:** 2026-10-15
* **Deciders:** Rudolfo Félix (AI Engineer)
* **Technical Story:** [RFC-001](../rfc/RFC-001-agentic-data-assistant.md)

---

## Context & Problem Statement
Requirement 2 strictly forbids displaying raw Personally Identifiable Information (PII) — such as customer names, emails, and IP addresses from `thelook_ecommerce.users` — to the executive user.
In production cloud environments, Google Cloud Sensitive Data Protection (Cloud DLP API) is commonly used, but it incurs substantial per-GB inspection costs ($1.00–$3.00/GB) and adds network latency to every LLM turn.

## Decision Drivers
* Zero-latency PII sanitization.
* FinOps cost control (zero external API fee).
* Deterministic reliability: regex/NLP logic must never hallucinate or fail silently.

## Considered Options
1. **Deterministic Regex & Microsoft Presidio Pattern (Selected for Prototype):** Runs in-process in Python, sanitizing emails (`\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b`), IPs, and user entities with zero network latency and $0 cost.
2. **Google Cloud DLP API:** Highly scalable for unstructured storage scans, but requires GCP service account permissions, active billing, and adds ~200-500ms network latency per query.
3. **Pure LLM Prompt Instruction ("Do not output emails"):** Extremely unreliable; prone to prompt injection, jailbreaks, and stochastic leakage.

## Decision Outcome
Adopt **in-process deterministic PII sanitization (Presidio-inspired regex and entity masking)** in `src/guardrails/pii.py` for the prototype. In the production HLD, specify a two-tier defense:
1. **Database Layer:** BigQuery Row-Level Security (RLS) + Dynamic Data Masking (DDM) hashing/nullifying columns at source.
2. **Gateway Layer:** In-process deterministic scrubber intercepting responses before rendering.

### Positive Consequences
* Zero runtime cost ($0.00).
* Sub-millisecond execution time with zero network dependencies.
* Robust defense-in-depth: Even if the LLM attempts to output customer emails, the sanitizer gate scrubs them before display.

### Negative / Neutral Consequences
* Highly complex, obscure unstructured PII (e.g. edge-case international phone formats) may require fine-tuned NER models in production.
