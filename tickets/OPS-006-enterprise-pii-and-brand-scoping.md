## OPS-006: Enterprise PII Sanitizer Gate & User Brand Scoping
Status: backlog  
Branch: feat/OPS-006-pii-scoping-guardrails  
Priority: Critical  

### Overview
Implement enterprise security and privacy guardrails: deterministic PII redaction (scrubbing emails, customer names, and IP addresses) and row-level brand authorization injection (`src/guardrails/`), handling multi-table join nuances cleanly.

### Goal
Enforce GDPR data minimization and prevent cross-tenant data leaks between category directors (Marcus persona).

### Description
- Implement `src/guardrails/pii.py` using deterministic regex and NLP patterns to mask customer names, emails (`[EMAIL_REDACTED]`), and IP addresses (`[IP_REDACTED]`) from dataframes and final executive reports.
- Implement `src/guardrails/scope.py` inspecting user context (`allowed_brands`) and injecting `WHERE brand IN (...)` into SQL queries.
- **Conditional Scoping Nuance (Mitigation 2):** Scoping guard detects whether the query accesses product/transaction metrics. If querying pure `users` demographics, it avoids appending non-existent `brand` column filters to the `users` table, preventing BigQuery 400 errors.

### Acceptance Criteria
1. Given raw BigQuery rows containing customer emails or IP addresses, the PII sanitizer scrubs all sensitive identifiers before display.
2. Given a user session scoped to specific brands (e.g. `['Calvin Klein', 'Tommy Hilfiger']`), generated SQL enforces brand restrictions.
3. Pure user demographic queries without product joins execute without invalid `brand` column syntax errors.
4. Redaction operates in-process with zero external API latency or costs.

### Implementation & Architecture
- 📄 **Related ADR:** [ADR-0005](../docs/adr/0005-presidio-pii-masking-vs-cloud-dlp.md)
- 📄 **Technical Spec:** [RFC-001](../docs/rfc/RFC-001-agentic-data-assistant.md) §3.4
- 📄 **PRD Requirements:** [PRD-RETAIL-ASSISTANT.md](../docs/prd/PRD-RETAIL-ASSISTANT.md) (FR-2, FR-3)

### Completion Criteria
1. `src/guardrails/pii.py` and `src/guardrails/scope.py` implemented.
2. Verified with unit tests in `tests/test_pii_masking.py` and `tests/test_scoping.py`.
