# RFC: OPS-003 - LangGraph State Schema & GoogleSQL Generation Node

**Related Ticket:** [OPS-003](../../tickets/OPS-003-langgraph-state-and-sql-generator.md)  
**General Runbook:** [Autonomous Swarm Protocol](../architecture/AUTONOMOUS_SWARM_PROTOCOL.md)
**Architectural References:** [ADR-0001](../adr/0001-adopt-langgraph-state-machine.md), [ADR-0007](../adr/0007-domain-driven-semantic-layer-for-text-to-sql.md), [ONT-001](../architecture/01_BUSINESS_ONTOLOGY_AND_UBIQUITOUS_LANGUAGE.md)

---

## 1. Executive Summary & Architectural Context

This RFC details the specification and implementation plan for the **LangGraph State Schema** (`src/agent/state.py`), the **Domain-Driven Prompting Engine** (`src/agent/prompts.py`), and the **GoogleSQL Generation Node** (`src/agent/nodes/generate_sql.py`).

The primary architectural objective is to establish the core state machine graph foundation and the deterministic Text-to-SQL translation pipeline using Google Gemini (`gemini-2.5-flash` default via `google-genai`). The system bridges the "semantic gap" by injecting the formal retail business ontology (`ONT-001`) and few-shot exemplars, ensuring mathematical consistency across Net Revenue, Margins, and Churn calculations while enforcing strict token efficiency and call budgets ($\le 5$ calls per user interaction).

---

## 2. Technical Specification & Design

### 2.1 LangGraph State Schema (`AgentState`)

The state schema is defined as a `TypedDict` in `src/agent/state.py`, containing all persistent and transient attributes required across the end-to-end multi-node graph:

```python
class AgentState(TypedDict):
    # Session & Identity Context
    user_query: str
    user_id: str
    session_id: str
    allowed_brands: list[str]

    # SQL Iteration & Self-Correction
    current_sql: str
    sql_history: list[str]
    error_feedback: str | None
    retry_count: int

    # Data & Results
    query_results: list[dict[str, Any]] | None
    sanitized_results: list[dict[str, Any]] | None

    # HITL Oversight (EU AI Act Art. 14)
    requires_confirmation: bool
    confirmation_status: bool | None

    # Reporting & Insights
    executive_report: str | None

    # FinOps Telemetry & Budgets
    total_llm_calls: int
    tokens_consumed: int
```

**State Guarantees:**
- Pre-allocates fields needed by downstream tickets (`sanitized_results` for OPS-006, `requires_confirmation` for OPS-007, `executive_report` for OPS-005) to eliminate breaking state migrations.
- `sql_history` maintains an audit trail of generated SQL iterations for post-execution tracing and debugging.

---

### 2.2 Semantic Prompting Engine (`src/agent/prompts.py`)

The prompt builder incorporates three layers of contextual guidance:
1. **Dynamic Schema Context:** Formatted Markdown schema from `SchemaInspector.format_schema_for_prompt()`, detailing all target tables (`orders`, `order_items`, `products`, `users`) and column types.
2. **Retail Business Ontology (`ONT-001`):**
   - **Net Revenue Rule:** `SUM(sale_price) WHERE status NOT IN ('Cancelled', 'Returned')`.
   - **Gross Profit Margin Rule:** Join `order_items` with `products` on `product_id`, compute `(sale_price - cost)` and `SAFE_DIVIDE(profit, revenue) * 100`.
   - **Customer Churn Rule:** Customer who placed $\ge 1$ order historically but has zero orders in trailing 90 days (`MAX(created_at) < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAY)`).
   - **Average Order Value (AOV):** `SAFE_DIVIDE(net_revenue, COUNT(DISTINCT order_id))`.
3. **Table Qualification & Brand Scoping Guardrails:**
   - Always qualify tables with `bigquery-public-data.thelook_ecommerce.<table>`.
   - If `allowed_brands` is provided and the query accesses products or product-joined tables, enforce `WHERE brand IN (...)` (or join alias `p.brand IN (...)`).
   - If the query targets only the `users` table (demographics, state counts), brand scoping is conditionally bypassed to avoid hallucinated column errors.
4. **Few-Shot Golden Bucket Exemplars:** 3 canonical pairs of Natural Language $\rightarrow$ GoogleSQL.
5. **Output Cleanliness:** Enforce raw SQL output without markdown ticks (`` ` ``) or conversational fluff.

---

### 2.3 SQL Generation Node (`src/agent/nodes/generate_sql.py`)

The node handles:
1. Constructing the prompt from `AgentState`.
2. Calling Google Gemini (`gemini-2.5-flash` or configured `settings.model_name`) using `google-genai` SDK.
3. Applying `@retry_with_backoff` decorator to automatically handle HTTP 429 rate limits with exponential backoff and jitter.
4. Sanitizing LLM output to strip markdown code blocks (```` ```sql ````, ```` ``` ````).
5. Updating state:
   - `state["current_sql"] = sanitized_sql`
   - `state["sql_history"].append(sanitized_sql)`
   - `state["total_llm_calls"] += 1`
   - Tracking `tokens_consumed` when available.

---

## 3. Execution Steps

1. **Step 1: Implement `src/agent/state.py`:**
   - Define `AgentState` TypedDict and default factory helper `create_initial_state(...)`.
2. **Step 2: Implement `src/agent/prompts.py`:**
   - System prompts, ontology definitions, Golden Bucket Trios, and prompt formatting functions.
3. **Step 3: Implement `src/agent/nodes/generate_sql.py`:**
   - Gemini API integration with rate-limit resilience, markdown stripping, and call accounting.
4. **Step 4: Author `tests/test_sql_generation.py`:**
   - Hermetic unit tests validating state integrity, prompt generation, markdown stripping, ontology compliance, brand scoping, and call counting.
5. **Step 5: Evidence & Subagent Review:**
   - Persist evidence in `tests/evidence/OPS-003/`.
   - Spawn QA & PO Auditor subagent.
