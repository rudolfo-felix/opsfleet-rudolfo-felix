## OPS-001: Repository Scaffolding, Pinned Dependencies & Config
Status: backlog  
Branch: feat/OPS-001-scaffolding  
Priority: High  

### Overview
Establish the foundational Python project layout, pinned dependencies, environment variables template, and centralized configuration loader.

### Goal
Ensure any evaluator can clone the repository, install dependencies in a virtual environment, and run configuration checks in under 2 minutes without missing package errors.

### Acceptance Criteria
1. Given a fresh virtual environment, when running `pip install -r requirements.txt`, all required libraries (`langgraph`, `langchain-google-genai`, `google-cloud-bigquery`, `rich`, `pydantic-settings`, `python-dotenv`) install cleanly without version conflicts.
2. Given `.env.example`, when inspected, all required variables (`GEMINI_API_KEY`, `MODEL_NAME`, `GCP_PROJECT_ID`, `MOCK_BIGQUERY`) are clearly documented with default fallback values (`MODEL_NAME=gemini-2.5-flash`).
3. Given `src/config.py`, when loaded, configuration variables are validated using Pydantic, raising clear descriptive errors if `GEMINI_API_KEY` is missing.

### Implementation & Architecture
* 📄 **Related ADR:** [ADR-0006](../docs/adr/0006-configurable-gemini-flash-and-rate-limit-backoff.md)
* 📄 **Technical Spec:** [RFC-001](../docs/rfc/RFC-001-agentic-data-assistant.md)

### Completion Criteria
1. `requirements.txt` and `.env.example` created and committed.
2. `src/config.py` implemented and unit tested.
3. Verified clean execution with `python3 -c "import src.config"`.
