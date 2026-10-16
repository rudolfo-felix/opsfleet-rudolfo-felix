## OPS-001: Repository Scaffolding, Pydantic Config & Rate-Limit Backoff
Status: done  
Branch: feat/OPS-001-scaffolding  
Priority: High  

### Overview
Initialize the Python 3.11+ development environment, establish pinned production dependencies, create `.env.example`, configure typed application settings with `pydantic-settings`, and implement a reusable exponential backoff decorator for Google AI Studio HTTP 429 (`RESOURCE_EXHAUSTED`) rate limits.

### Goal
Deliver a clean, reproducible project structure adhering to Vlad Bondarenko's requirement for zero-crash execution under personal API keys.

### Description
- Configure `pyproject.toml` supporting editable installation (`pip install -e .`) and tool configurations (`pytest`, `ruff`).
- Configure `requirements.txt` with consolidated pinned dependencies: `langgraph`, `google-genai`, `google-cloud-bigquery`, `pandas`, `pyarrow`, `db-dtypes`, `duckdb`, `rich`, `pydantic-settings`, `python-dotenv`, `pytest`, `presidio-analyzer`, `presidio-anonymizer`, `opentelemetry-api`, `opentelemetry-sdk`. Essential: `pandas`, `pyarrow`, and `db-dtypes` prevent runtime `ImportError` on `BigQuery.query().to_dataframe()`.
- Create `.env.example` documenting `GEMINI_API_KEY`, `MODEL_NAME` (defaulting to `gemini-2.5-flash`), `GCP_PROJECT_ID`, and `MOCK_BIGQUERY`.
- Implement `src/config.py` using `BaseSettings` validating environment configuration. Missing `GEMINI_API_KEY` raises a friendly, formatted validation error.
- Implement `src/agent/resilience.py` providing `@retry_with_backoff(max_retries=3, initial_delay=1.0, factor=2.0, jitter=True)` catching HTTP 429 (`RESOURCE_EXHAUSTED`) with exponential backoff (distinct from the graph's SQL self-correction cap).
- Create `tests/conftest.py` with shared pytest fixtures (`mock_gemini_response`, `sample_agent_state`, `mock_bq_rows`).

### Acceptance Criteria
1. Given a fresh environment, both `pip install -r requirements.txt` and `pip install -e .` succeed without compilation errors.
2. Given `.env.example`, all settings are documented with defaults (`MODEL_NAME=gemini-2.5-flash`).
3. Given `src/config.py`, loading configuration without `GEMINI_API_KEY` raises a friendly, handled validation error rather than an unhandled traceback crash.
4. Given Google AI Studio HTTP 429 exceptions, `@retry_with_backoff` catches the error, logs a terminal alert, and retries up to `max_retries=3` times with exponential backoff and jitter.

### Implementation & Architecture
- 📄 **Related ADR:** [ADR-0006](../docs/adr/0006-configurable-gemini-flash-and-rate-limit-backoff.md)
- 📄 **Technical Spec:** [RFC-001](../docs/rfc/RFC-001-agentic-data-assistant.md) §4.3

### Completion Criteria
1. `pyproject.toml`, `requirements.txt`, `.env.example`, `src/config.py`, `src/agent/resilience.py`, and `tests/conftest.py` implemented.
2. Verified with `pytest tests/test_config.py tests/test_resilience.py`.
