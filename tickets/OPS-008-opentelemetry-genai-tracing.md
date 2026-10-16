## OPS-008: OpenTelemetry GenAI Telemetry & Token Accounting
Status: backlog  
Branch: feat/OPS-008-otel-telemetry  
Priority: Medium  

### Overview
Implement enterprise observability adhering to OpenTelemetry GenAI Semantic Conventions (`gen_ai.*`). Capture structured spans for agent execution nodes, track latency attribution, count input/output tokens, and maintain a query call counter enforcing Vlad Bondarenko's 2–5 calls FinOps budget.

### Goal
Provide senior technical reviewers (Vlad Bondarenko) with complete execution transparency without leaking PII or raw database rows into telemetry attributes.

### Description
- Implement `src/telemetry/tracer.py` managing OpenTelemetry spans and metrics.
- Track standard GenAI attributes: `gen_ai.system="gemini"`, `gen_ai.request.model`, `gen_ai.usage.prompt_tokens`, `gen_ai.usage.completion_tokens`.
- Track node latencies (SQL generation time, BigQuery execution time, synthesis time).
- Maintain `call_counter` per user session asserting total calls per turn remain within 2–5 calls.
- Sanitize telemetry attributes: ensure raw database customer records and user queries never leak into standard span attributes.

### Acceptance Criteria
1. Executing any analytical query emits structured telemetry logs with accurate latency and token metrics.
2. Token consumption and LLM call counts are tracked per turn and aggregated for session analytics.
3. Telemetry conforms to CNCF OpenTelemetry GenAI semantic conventions.
4. No sensitive customer PII is present in span metadata.

### Implementation & Architecture
- 📄 **Related ADR:** [ADR-0002](../docs/adr/0002-adopt-langfuse-oss-for-observability.md)
- 📄 **Technical Spec:** [RFC-001](../docs/rfc/RFC-001-agentic-data-assistant.md) §3.6

### Completion Criteria
1. `src/telemetry/tracer.py` implemented.
2. Verified with unit tests in `tests/test_telemetry.py`.
