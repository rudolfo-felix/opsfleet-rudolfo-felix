## OPS-001: Repository Scaffolding, Pydantic Config & Rate-Limit Backoff
Status: backlog  
Branch: feat/OPS-001-scaffolding  
Priority: High  

### Overview
Initialize the Python 3.11+ development environment, establish pinned production dependencies, create `.env.example`, configure typed application settings with `pydantic-settings`, and implement a reusable exponential backoff decorator for Google AI Studio HTTP 429 (`RESOURCE_EXHAUSTED`) rate limits.

### Goal
Deliver a clean, reproducible project structure adhering to Vlad Bondarenko's requirement for zero-crash execution under personal API keys.

### Description
- Configure `requirements.txt` with pinned dependencies: `langgraph`, `google-genai`, `google-cloud-bigquery`, `duckdb`, `rich`, `pydantic-settings`, `python-dotenv`, `pytest`.
- Create `.env.example` documenting `GEMINI_API_KEY`, `MODEL_NAME` (defaulting to `gemini-2.5-flash`), `GCP_PROJECT_ID`, and `MOCK_BIGQUERY`.
- Implement `src/config.py` using `BaseSettings` validating environment configuration.
- Implement `src/agent/resilience.py` providing `@retry_with_backoff` with exponential delays and jitter.

### Acceptance Criteria
1. Given a fresh environment, `pip install -r requirements.txt` succeeds without compilation errors.
2. Given `.env.example`, all settings are documented with defaults (`MODEL_NAME=gemini-2.5-flash`).
3. Given `src/config.py`, loading configuration without `GEMINI_API_KEY` raises a friendly validation error rather than an unhandled crash.
4. Given Google AI Studio HTTP 429 exceptions, `@retry_with_backoff` catches the error, logs a terminal alert, and retries up to 3 times with exponential backoff and jitter.

### Implementation & Architecture
- 📄 **Related ADR:** [ADR-0006](../docs/adr/0006-configurable-gemini-flash-and-rate-limit-backoff.md)
- 📄 **Technical Spec:** [RFC-001](../docs/rfc/RFC-001-agentic-data-assistant.md) §4.3

### Completion Criteria
1. `requirements.txt`, `.env.example`, `src/config.py`, and `src/agent/resilience.py` implemented.
2. Verified with `pytest tests/test_config.py tests/test_resilience.py`.
