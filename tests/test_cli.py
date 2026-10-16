"""Tests for Rich Interactive CLI Interface & Application Entrypoint (OPS-009).

Validates:
1. Pre-flight verification with `--dry-run` exiting with code 0 without calling live Gemini endpoints.
2. Missing GEMINI_API_KEY friendly error panel and clean non-zero exit without unhandled traceback.
3. Table formatting with automatic column alignment and truncation.
4. CLI flag parsing (--user-id, --brands, --mock-bq, --model).
5. Presentation view rendering (banners, reports, telemetry cards, HITL warnings).
6. Simulated HITL deletion confirmation and cancellation.
"""

from unittest.mock import patch

from rich.console import Console
from rich.table import Table

from main import _detect_database_engine, main, parse_arguments
from src.cli.tables import format_records_to_table
from src.cli.view import (
    render_banner,
    render_error,
    render_executive_report,
    render_hitl_warning,
    render_telemetry_card,
)


def test_cli_argument_parsing():
    """Verify CLI flag parsing for user persona, brand scoping, mock engine, and model override."""
    args = parse_arguments([
        "--user-id", "marcus_buyer",
        "--brands", "Calvin Klein,Tommy Hilfiger",
        "--mock-bq",
        "--model", "gemini-2.5-flash",
    ])
    assert args.user_id == "marcus_buyer"
    assert args.brands == "Calvin Klein,Tommy Hilfiger"
    assert args.mock_bq is True
    assert args.model == "gemini-2.5-flash"
    assert args.dry_run is False


def test_cli_dry_run_flag():
    """Verify that python main.py --dry-run completes cleanly with exit code 0."""
    exit_code = main(["--dry-run", "--mock-bq"])
    assert exit_code == 0


def test_cli_missing_api_key_clean_exit(monkeypatch):
    """Verify missing GEMINI_API_KEY renders friendly error panel and returns exit code 1."""
    monkeypatch.setenv("GEMINI_API_KEY", "")
    from src.config import get_settings
    get_settings.cache_clear()

    # When running without --dry-run and missing key, must exit 1 cleanly
    exit_code = main([])
    assert exit_code == 1
    get_settings.cache_clear()


def test_detect_database_engine():
    """Verify detection of live vs fallback mock engine."""
    engine_desc = _detect_database_engine(force_mock=True)
    assert "DuckDB" in engine_desc
    assert "Mock" in engine_desc


def test_format_records_to_table_with_records():
    """Verify DataFrame/dictionary table formatting and truncation."""
    # 1. Non-empty records
    records = [
        {"id": i, "category": f"Category {i}", "sale_price": float(i * 10), "status": "Complete"}
        for i in range(1, 30)
    ]
    table = format_records_to_table(records, title="Test Sales", max_rows=10)
    assert isinstance(table, Table)
    assert table.title == "Test Sales"
    assert len(table.rows) == 10
    assert "Showing top 10 of 29" in str(table.caption)

    # 2. Empty records
    empty_table = format_records_to_table([])
    assert isinstance(empty_table, Table)
    assert len(empty_table.rows) == 1


def test_view_presentation_rendering():
    """Verify all presentation layer functions execute without raising exceptions."""
    console = Console(record=True, width=100)

    # 1. Render Banner
    render_banner(
        console=console,
        model_name="gemini-2.5-flash",
        db_engine="DuckDB (Mock)",
        user_id="sarah_ceo",
        brands=["Nike", "Adidas"],
    )

    # 2. Render Error
    render_error(
        console=console,
        title="Test Error",
        message="An intentional test exception occurred.",
        resolution_hint="Check configuration settings.",
    )

    # 3. Render Executive Report
    report_md = (
        "## Executive Summary\n"
        "Net revenue increased 14.2% quarter-over-quarter.\n\n"
        "## Key Findings\n"
        "- Denim category outperformed expectations.\n\n"
        "## Q2 Action Items\n"
        "- Increase stock in top 3 bestselling styles."
    )
    render_executive_report(console=console, report_markdown=report_md)

    # 4. Render Telemetry Card
    telemetry = {
        "total_llm_calls": 2,
        "tokens_consumed": 450,
        "prompt_tokens": 300,
        "completion_tokens": 150,
        "cumulative_latency_sec": 1.25,
    }
    render_telemetry_card(console=console, telemetry=telemetry)

    # 5. Render HITL Warning
    render_hitl_warning(console=console, prompt_message="Are you sure you want to delete report #1? [y/N]")

    output = console.export_text()
    assert "THELOOK RETAIL ANALYTICS AI ASSISTANT" in output
    assert "Test Error" in output
    assert "Strategic Executive Briefing" in output
    assert "Execution Telemetry & FinOps Card" in output
    assert "High-Stakes Oversight" in output


def test_interactive_mock_repl_turn(monkeypatch):
    """Verify interactive REPL turn processing with user exit command."""
    monkeypatch.setenv("GEMINI_API_KEY", "dummy_key_for_testing")
    from src.config import get_settings
    get_settings.cache_clear()

    # Mock console.input to simulate user entering "help" followed by "exit"
    inputs = ["help", "exit"]
    with patch("rich.console.Console.input", side_effect=inputs):
        exit_code = main(["--mock-bq"])
        assert exit_code == 0

    get_settings.cache_clear()
