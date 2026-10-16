# RFC: OPS-001 - Repository Scaffolding, Pydantic Config & Rate-Limit Backoff

* **Related Ticket:** [OPS-001](../../tickets/OPS-001-scaffolding-config-resilience.md)  
* **Parent Architecture:** [RFC-001 §4.3](RFC-001-agentic-data-assistant.md)  
* **Related ADR:** [ADR-0006](../adr/0006-configurable-gemini-flash-and-rate-limit-backoff.md)  
* **Author:** AI Systems Architect & Software Engineer  
* **Status:** Implemented & Verified  
* **Date:** 2026-10-16  

---

## Technical Specification

This technical specification details the complete engineering design, interfaces, error-handling contracts, and step-by-step code execution for the foundation scaffolding of the **Retail Data Analysis AI Assistant**.

### 1. Prerequisites & Architectural Invariants
* **Invariant 1 (The 2-Minute Evaluator Rule):** Evaluator Vlad Bondarenko must be able to clone the repo, populate `GEMINI_API_KEY` in `.env`, and run `python main.py` in < 2 minutes with zero dependency compilation failures or unhandled tracebacks.
* **Invariant 2 (Model Configurability):** Default model `gemini-2.5-flash`, configurable via `MODEL_NAME` in `.env`, rejecting retired models (`gemini-1.5`) or paid models (`gemini-pro`).
* **Invariant 3 (Rate Limit Resilience):** Exponential backoff with jitter on HTTP 429 (`RESOURCE_EXHAUSTED`).
* **Invariant 12 (Evidence-Based Verification Gate):** Execution evidence (pytest, ruff, CLI demo) must be saved in `tests/evidence/OPS-001/`.
* **Invariant 13 (Zero Dev-Cost Bias):** Strict typing, explicit Pydantic `BaseSettings`, clean error boundaries.

---

### 2. Interface & Component Design

#### 2.1 Dependency Management (`pyproject.toml` & `requirements.txt`)
* Build backend: `setuptools>=61.0`.
* Python constraint: `>=3.11`.
* Critical packages:
  - `langgraph>=0.2.20` & `langchain-core>=0.3.0` (core cyclic state machine)
  - `google-genai>=0.1.1` (official Google Gemini SDK)
  - `google-cloud-bigquery>=3.25.0`
  - `pandas>=2.2.0`, `pyarrow>=15.0.0`, `db-dtypes>=1.2.0` (mandatory runtime dependencies preventing `ImportError` on `BigQuery.query().to_dataframe()`)
  - `duckdb>=1.0.0` (in-memory offline mock engine)
  - `pydantic-settings>=2.2.0` & `pydantic>=2.7.0` (12-factor configuration)
  - `rich>=13.7.0` (terminal UX & alert formatting)
  - `presidio-analyzer>=2.2.355` & `presidio-anonymizer>=2.2.355` (PII masking)
  - `opentelemetry-api>=1.24.0` & `opentelemetry-sdk>=1.24.0` (GenAI semantic spans)

#### 2.2 Environment Configuration Schema (`src/config.py`)
```python
class Settings(BaseSettings):
    # Google AI Studio
    gemini_api_key: str = Field(default="")
    model_name: str = Field(default="gemini-2.5-flash")

    # BigQuery
    gcp_project_id: str = Field(default="bigquery-public-data")
    mock_bigquery: bool = Field(default=False)

    # FinOps & Operational Budgets
    max_llm_calls_per_query: int = Field(default=5, ge=1, le=10)
    max_sql_retries: int = Field(default=2, ge=0, le=5)
    backoff_max_retries: int = Field(default=3, ge=1, le=10)
    backoff_initial_delay: float = Field(default=1.0, gt=0.0)
    backoff_factor: float = Field(default=2.0, ge=1.0)
    backoff_jitter: bool = Field(default=True)

    # Storage & Telemetry
    storage_db_path: str = Field(default="reports.db")
    log_level: str = Field(default="INFO")
    otel_enabled: bool = Field(default=False)
```

#### 2.3 Handled Error Boundary on Missing `GEMINI_API_KEY`
Instead of an unhandled traceback or generic exception, `load_settings()` intercepts empty/missing keys and raises `ConfigurationError` formatting a prominent terminal alert:
```text
┌────────────────────────────────────────────────────────────────────────┐
│ ⚠️  MISSING GEMINI_API_KEY                                              │
├────────────────────────────────────────────────────────────────────────┤
│ The retail assistant requires a Google Gemini API key to operate.     │
│                                                                        │
│ 1. Get a free API key at: https://aistudio.google.com/                 │
│ 2. Create a .env file from .env.example:                              │
│      cp .env.example .env                                              │
│ 3. Add your key:                                                       │
│      GEMINI_API_KEY=AIzaSy...                                          │
└────────────────────────────────────────────────────────────────────────┘
```

#### 2.4 Exponential Backoff & Jitter Decorator (`src/agent/resilience.py`)
* Mathematical formula:
  $$\text{delay} = \min(\text{max\_delay}, \text{initial\_delay} \times \text{factor}^{\text{attempt}}) \pm \text{Uniform}(0, 0.5)$$
* Error trapping: Intercepts HTTP 429 status codes, `RESOURCE_EXHAUSTED`, and Google API `ResourceExhausted` errors.
* Terminal feedback: Logs yellow Rich warning `Google AI Studio rate limit reached (HTTP 429). Backing off for Xs (Attempt Y/3)...` without interrupting workflow.
* Function signature support: Fully supports both synchronous (`def`) and asynchronous (`async def`) callables.

---

### 3. Step-by-Step Execution Steps

1. **Step 1 (Packaging & Dependencies):**
   - Author `requirements.txt` with pinned versions.
   - Author `pyproject.toml` supporting `pip install -e .` and configuring `pytest` and `ruff`.
   - Author `.env.example` documenting all configuration keys.
2. **Step 2 (Configuration Module):**
   - Author `src/config.py` with `Settings` and `load_settings()`.
   - Add model validation rejecting retired models and paid models.
   - Add handled `ConfigurationError` alert box.
3. **Step 3 (Rate-Limit Resilience):**
   - Author `src/agent/resilience.py` with `is_rate_limit_error`, `calculate_backoff_delay`, and `@retry_with_backoff`.
4. **Step 4 (Test Harness & Evidence):**
   - Author `tests/conftest.py` with `sample_agent_state`, `mock_gemini_response`, and `mock_bq_rows`.
   - Author `tests/test_config.py` (7 tests).
   - Author `tests/test_resilience.py` (6 tests).
   - Execute test suite and verify 100% pass rate.
   - Capture execution logs into `tests/evidence/OPS-001/`.
5. **Step 5 (Code Quality & Formatting):**
   - Run `ruff check` and `ruff format` ensuring 0 lints.

---

### 4. Verification & Evidence
* **Unit Tests:** 13/13 passing in 0.08s.
* **Linter:** `ruff check` passes with 0 errors.
* **Evidence Directory:** `tests/evidence/OPS-001/` contains:
  - `pytest_output.txt`
  - `ruff_output.txt`
  - `execution_demo.txt` (demonstrating handled error box, backoff calculation, and settings loading).
