# RFC: OPS-008 - OpenTelemetry GenAI Telemetry & Token Accounting

**Related Ticket:** [OPS-008](../../tickets/OPS-008-opentelemetry-genai-tracing.md)  
**General Runbook:** [Autonomous Swarm Protocol](../architecture/AUTONOMOUS_SWARM_PROTOCOL.md)  
**Architectural Baseline:** [ADR-0002](../adr/0002-adopt-langfuse-oss-for-observability.md), [PRD-RETAIL-ASSISTANT.md](../prd/PRD-RETAIL-ASSISTANT.md) (NFR-3)

---

## 1. Technical Specification & Context

### 1.1 Problem Statement
Requirement 7 demands enterprise observability for all agent interactions, capturing execution trajectories, node latencies, and token consumption metrics. Furthermore, Vlad Bondarenko's Slack directive mandates enforcing a strict **2–5 LLM calls per query budget** to avoid token burn and latency bloat.

However, enterprise retail deployments introduce two strict operational constraints:
1. **Zero External Collector Friction (Invariant 1):** Evaluators must be able to run `python main.py` or `pytest` immediately without standing up an external Jaeger, Prometheus, or Langfuse daemon.
2. **Defensive PII Isolation in Metadata (Invariant 9):** Telemetry attributes must never contain unmasked customer PII (`first_name`, `last_name`, `email`, `ip_address`) or raw tabular database records.

### 1.2 Proposed Architecture
Implement `src/telemetry/tracer.py` providing a clean, enterprise OpenTelemetry integration adhering to CNCF GenAI Semantic Conventions:
- **Tracer Provider & Processors:** Configurable OpenTelemetry `TracerProvider`. When running locally without an OTLP endpoint, uses `InMemorySpanExporter` or `ConsoleSpanExporter` wrapped in a thread-safe context manager.
- **Semantic Conventions:**
  - `gen_ai.system = "gemini"`
  - `gen_ai.request.model = settings.model_name`
  - `gen_ai.operation.name = "generate_content"` / `"execute_sql"` / `"synthesize"`
  - `gen_ai.usage.prompt_tokens = int`
  - `gen_ai.usage.completion_tokens = int`
  - `gen_ai.usage.total_tokens = int`
  - `gen_ai.retail.llm_call_count = int`
- **Span Hierarchy:**
  - Root span: `retail_agent.turn`
  - Node spans: `agent.generate_sql`, `agent.execute_sql`, `agent.sanitize_pii`, `agent.synthesize`, `agent.reports`
- **FinOps Call & Token Accountant (`FinOpsTracker`):**
  - Tracks cumulative prompt tokens, completion tokens, call count, and node latencies per turn.
  - Generates structured turn summaries for CLI display and evaluation assertions (`assert 2 <= total_calls <= 5`).
- **Defensive PII Redaction Filter:**
  - Before injecting query text or prompt context into span attributes, executes `sanitize_text()` to guarantee zero customer identifiers leak to trace collectors.

---

## 2. Prerequisites & Invariants
- **Invariant 1 (2-Minute Rule):** Pure standard OpenTelemetry SDK with in-memory / logging fallbacks. No external collectors required for local runs.
- **Invariant 4 (FinOps Budget):** `llm_calls_per_turn` tracked and verified against `settings.max_llm_calls_per_query` (default 5).
- **Invariant 9 (PII Guardrail):** No unmasked customer attributes allowed in span events or attributes.
- **ADR-0002 (Open Standards):** CNCF `gen_ai.*` convention compliance ensuring seamless portability to Langfuse OSS or Google Cloud Trace.

---

## 3. Execution Steps & Module Breakdown

### Step 1: Telemetry Core Module (`src/telemetry/tracer.py`)
- Define `get_tracer(service_name="thelook-retail-assistant") -> trace.Tracer`.
- Define `FinOpsTracker` dataclass tracking:
  - `user_id: str`
  - `session_id: str`
  - `total_llm_calls: int`
  - `prompt_tokens: int`
  - `completion_tokens: int`
  - `node_latencies: dict[str, float]`
- Provide context manager `@trace_node(node_name: str)` or `with start_genai_span(...)` capturing execution duration, setting span status, and recording `gen_ai.*` attributes.
- Sanitize all string attributes using `src.guardrails.pii.sanitize_text`.

### Step 2: LangGraph Node Instrumentations
- Integrate tracing context or decorator within `generate_sql`, `execute_sql`, `sanitize_pii`, `synthesize`, and `reports_node` without altering their functional output contracts.
- Ensure token counts from Gemini API responses (or synthetic token estimators when running offline) are reported into the active span.

### Step 3: Verification & Unit Tests (`tests/test_telemetry.py`)
- Unit test span creation using `InMemorySpanExporter`.
- Test verification of standard GenAI attributes (`gen_ai.system`, `gen_ai.request.model`, `gen_ai.usage.*`).
- Test latency recording and duration > 0.
- Test FinOps budget assertions (verifying calls remain within 2–5).
- Test defensive scrubbing (ensuring emails and names injected in queries are scrubbed in span attributes).
