## OPS-009: Rich Interactive CLI Interface & Application Entrypoint (`main.py`)
Status: backlog  
Branch: feat/OPS-009-rich-cli-main  
Priority: High  

### Overview
Build an interactive terminal chat interface using `rich` featuring executive banners, live status spinners, formatted markdown tables, and a dedicated telemetry panel. Implement the top-level application entrypoint (`main.py`) supporting CLI flags (`--user-id`, `--brands`, `--mock-bq`, `--dry-run`), satisfying the "2-Minute Clone-and-Run" evaluator rule.

### Goal
Deliver an intuitive, visually polished conversational experience for executive leadership and senior evaluators.

### Description
- Implement `src/cli/view.py` rendering welcome banners, model configuration info (active `MODEL_NAME`), and formatted executive reports.
- Implement `src/cli/tables.py` formatting pandas DataFrames into Rich terminal tables with automatic truncation.
- Implement spinners indicating active pipeline stages: *"Inspecting schema..."*, *"Running BigQuery SQL..."*, *"Synthesizing executive report..."*.
- Implement `main.py` tying together CLI argument parsing (`argparse`), `AgentState` initialization, interactive chat loop, and LangGraph HITL interrupt/resume handling.
- Display a concise execution telemetry card after each turn (latency, token consumption, call count, active database engine).

### Acceptance Criteria
1. Given `python main.py`, the CLI initializes cleanly, displaying active model and database engine status.
2. Given execution steps, spinners provide real-time visual progress without terminal screen flickering.
3. If Google AI Studio rate limits (HTTP 429) occur, a warning countdown is rendered cleanly without crashing or dumping tracebacks.
4. If `GEMINI_API_KEY` is missing, `main.py` displays a formatted error panel with instructions on acquiring a free key from Google AI Studio.

### Implementation & Architecture
- 📄 **Related ADR:** [ADR-0006](../docs/adr/0006-configurable-gemini-flash-and-rate-limit-backoff.md)
- 📄 **Technical Spec:** [RFC-001](../docs/rfc/RFC-001-agentic-data-assistant.md) §4
- 📄 **PRD Requirements:** [PRD-RETAIL-ASSISTANT.md](../docs/prd/PRD-RETAIL-ASSISTANT.md) (NFR-1)

### Completion Criteria
1. `src/cli/` and `main.py` implemented.
2. Verified interactive execution and automated test in `tests/test_cli.py`.
