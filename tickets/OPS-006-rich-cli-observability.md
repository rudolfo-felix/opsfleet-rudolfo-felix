## OPS-006: Rich Interactive CLI Interface & OTel-Compliant Telemetry
Status: backlog  
Branch: feat/OPS-006-cli-telemetry  
Priority: High  

### Overview
Build an interactive terminal chat interface using `rich` with live status spinners, formatted markdown tables, and structured telemetry adhering to OpenTelemetry GenAI semantic conventions (`gen_ai.*`), featuring clean exponential backoff on HTTP 429 rate limits.

### Goal
Deliver an intuitive conversational experience for executive users and provide senior evaluators with visible trace logs (e.g. `[PII MASKED]`, `[RETRY: Fixing SQL]`, `[OTel: 420 tokens]`).

### Acceptance Criteria
1. Given a user session, the CLI renders an executive banner, model configuration info, and a clean prompt interface.
2. Given execution steps, spinners indicate active progress: *"Inspecting schema..."*, *"Running BigQuery SQL..."*, *"Synthesizing executive report..."*.
3. Given Google AI Studio rate limits (HTTP 429 `RESOURCE_EXHAUSTED`), the CLI catches the exception and displays an exponential backoff countdown without crashing.
4. Given OpenTelemetry conventions, logs record latency per node and token usage while isolating PII data from span attributes.

### Implementation & Architecture
* 📄 **Related ADR:** [ADR-0002](../docs/adr/0002-adopt-langfuse-oss-for-observability.md) & [ADR-0006](../docs/adr/0006-configurable-gemini-flash-and-rate-limit-backoff.md)
* 📄 **Technical Spec:** [RFC-001](../docs/rfc/RFC-001-agentic-data-assistant.md)

### Completion Criteria
1. `src/cli.py` and `src/telemetry/tracer.py` implemented.
2. Verified interactive execution and rate-limit simulation.
