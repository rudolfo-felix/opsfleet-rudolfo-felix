## OPS-004: Enterprise PII Redaction & User Brand Scoping Guardrails
Status: backlog  
Branch: feat/OPS-004-pii-guardrails  
Priority: Critical  

### Overview
Implement enterprise safety controls: deterministic PII redaction (masking customer names, emails, IPs from the `users` table) and user scoping injection (restricting query results to the executive's allowed brands/categories).

### Goal
Comply with GDPR and EU AI Act data minimization standards by ensuring raw PII never reaches the executive's terminal, and enforcing row-level brand authorization.

### Acceptance Criteria
1. Given raw database rows containing `email`, `first_name`, `last_name`, or `ip_address`, the PII gate redacts them into masked tokens (e.g. `[EMAIL_REDACTED]`, `[IP_REDACTED]`).
2. Given an executive scoped to specific brands (e.g., `--brands "Calvin Klein,Nike"` or interactive selector), the agent enforces row-level filters in the SQL `WHERE` clause.
3. If an executive requests products outside their scope, the agent politely rejects or scopes the query explicitly to authorized brands.

### Implementation & Architecture
* 📄 **Related ADR:** [ADR-0005](../docs/adr/0005-presidio-pii-masking-vs-cloud-dlp.md)
* 📄 **Technical Spec:** [RFC-001](../docs/rfc/RFC-001-agentic-data-assistant.md)

### Completion Criteria
1. `src/guardrails/pii.py` and `src/guardrails/scope.py` implemented.
2. Verified with unit tests testing regex edge cases on emails, IPv4/IPv6, and names.
