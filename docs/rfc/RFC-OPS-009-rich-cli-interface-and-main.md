# RFC: OPS-009 - Rich Interactive CLI Interface & Application Entrypoint (`main.py`)

**Related Ticket:** [OPS-009](../../tickets/OPS-009-rich-cli-interface-and-main.md)  
**General Runbook:** [Autonomous Swarm Protocol](../architecture/AUTONOMOUS_SWARM_PROTOCOL.md)  
**Architectural Baseline:** [ADR-0006](../adr/0006-configurable-gemini-flash-and-rate-limit-backoff.md), [PRD-RETAIL-ASSISTANT.md](../prd/PRD-RETAIL-ASSISTANT.md) (NFR-1)

---

## 1. Technical Specification & Context

### 1.1 Problem Statement
Requirement 1 and Vlad Bondarenko's Slack directives dictate that senior evaluators must be able to clone the repository and run the application in under 2 minutes:
```bash
git clone <repo>
pip install -e .
python main.py
```
To satisfy this requirement without friction, the application entrypoint `main.py` must provide:
1. **Graceful Pre-flight Validation (Invariant 1):** Friendly, unhandled-traceback-free validation when `GEMINI_API_KEY` is unset or invalid, complete with a direct URL to Google AI Studio.
2. **Automated Validation via `--dry-run`:** A zero-network verification flag checking configuration parsing, schema inspection, database engine detection, and LangGraph StateGraph compilation before exiting cleanly with status code 0.
3. **Interactive Human-In-The-Loop (HITL) Console:** Seamless handling of LangGraph `interrupt()` during destructive report deletions (OPS-007), rendering formatted prompts and resuming via `Command(resume=...)`.
4. **Visually Polished Executive UX:** Clean Rich terminal panels, non-flickering status spinners, formatted markdown reports, and a concise FinOps telemetry summary card after every turn.

---

## 2. Prerequisites & Invariants
- **Invariant 1 (2-Minute Evaluator Rule):** Immediate startup with zero external container, collector, or database dependencies.
- **Invariant 2 (Model Configurability):** Honors `MODEL_NAME` environment variable (default: `gemini-2.5-flash`) and prints active model family in the banner.
- **Invariant 5 (Dual BigQuery Engine):** Detects GCP ADC and transparently displays whether Live BigQuery or In-Memory DuckDB Mock is active.
- **Invariant 10 (HITL Interrupt & MemorySaver):** Captures graph pauses at the CLI boundary, displays explicit warnings, and captures human confirmation input.
- **Invariant 4 (FinOps Accounting):** Renders turn call count, tokens consumed, and node latencies from `FinOpsTracker` after each query.

---

## 3. Architecture & Execution Steps

### Step 1: Presentation Layer (`src/cli/view.py` & `src/cli/tables.py`)
- `src/cli/view.py`:
  - `render_banner(model_name: str, db_engine: str, user_id: str, brands: list[str] | None)`: prints stylized ASCII / Rich panel with system details and helpful prompt hints.
  - `render_error(title: str, message: str, resolution_hint: str | None = None)`: formatted red panel with resolution steps.
  - `render_executive_report(report_markdown: str)`: parses and prints markdown with high-contrast styling.
  - `render_telemetry_card(telemetry_data: dict[str, Any])`: formatted compact table showing turn latency, total tokens, LLM calls, and budget status.
- `src/cli/tables.py`:
  - `format_records_to_table(records: list[dict[str, Any]], title: str = "Query Results", max_rows: int = 20) -> Table`: formats tabular records into a Rich Table with column styling, alternating row colors, and row count truncation.

### Step 2: Application Entrypoint (`main.py`)
- CLI Argument Parsing (`argparse`):
  - `--user-id`: string (default: `"executive_user"` or persona name).
  - `--brands`: comma-separated string of allowed brands (e.g., `"Calvin Klein,Tommy Hilfiger"`).
  - `--mock-bq`: boolean flag forcing DuckDB in-memory mock engine.
  - `--dry-run`: boolean flag running pre-flight verification and exiting 0.
- Interactive Session Loop:
  - Maintains `MemorySaver` checkpointer and unique `thread_id` per run.
  - Reads user input using `console.input("[bold green]TheLook > [/bold green]")`.
  - Uses `console.status("[bold cyan]Analyzing retail data...[/bold cyan]")` spinner during pipeline execution.
  - Evaluates `result`:
    - If `result.get("__interrupt__")`: displays EU AI Act Art. 14 prompt, captures human input, and resumes via `graph.invoke(Command(resume=answer), config=config)`.
    - Else: renders `executive_report`, tabular records, and telemetry card.
  - Handles `KeyboardInterrupt` and `EOFError` with clean exit.

### Step 3: Verification & Unit Tests (`tests/test_cli.py`)
- Unit test `--dry-run` flag: verify exit code 0 and proper banner rendering.
- Unit test missing API key: verify friendly error panel and clean exit without unhandled traceback.
- Unit test table formatting: verify truncation and column alignment.
- Unit test interactive mock turn: verify question to report and telemetry card rendering.
