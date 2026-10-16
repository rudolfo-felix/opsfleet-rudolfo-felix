"""Rich Presentation View Layer for Retail Data Analysis Assistant.

Renders executive terminal banners, Markdown reports, error alerts,
and FinOps telemetry summary cards.
"""

from typing import Any

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table


def render_banner(
    console: Console,
    model_name: str,
    db_engine: str,
    user_id: str,
    brands: list[str] | None = None,
) -> None:
    """Render executive welcome banner with system metadata and prompt guidance."""
    engine_badge = (
        "[bold green]Google Cloud BigQuery (Live Engine)[/bold green]"
        if "live" in db_engine.lower()
        else "[bold yellow]DuckDB (In-Memory Mock Fallback)[/bold yellow]"
    )
    brands_str = ", ".join(brands) if brands else "[dim]All Brands (Unrestricted)[/dim]"

    content = (
        f"[bold white]🛍️  THELOOK RETAIL ANALYTICS AI ASSISTANT[/bold white]\n"
        f"[dim]Executive Data Intelligence & Governance Platform[/dim]\n\n"
        f"• [bold]Model Family:[/bold]    [cyan]{model_name}[/cyan]\n"
        f"• [bold]Data Warehouse:[/bold]  {engine_badge}\n"
        f"• [bold]Active Persona:[/bold]  [magenta]{user_id}[/magenta]\n"
        f"• [bold]Scoped Brands:[/bold]   {brands_str}\n\n"
        f"[bold underline]Commercial Capabilities & Prompts:[/bold underline]\n"
        f"  [green]•[/green] [bold]Net Revenue:[/bold]     *'What was our Net Revenue by category last quarter?'*\n"
        f"  [green]•[/green] [bold]Brand Margins:[/bold]   *'Which brands have our highest gross margins?'*\n"
        f"  [green]•[/green] [bold]Customer Churn:[/bold]  *'How many customers churned over the last 90 days?'*\n"
        f"  [green]•[/green] [bold]Report Mgmt:[/bold]     *'Show saved reports'*, *'Save report'*, *'Delete report #2'*\n"
        f"  [green]•[/green] [bold]Session Exit:[/bold]    Type *'exit'*, *'quit'*, or press Ctrl+C to close."
    )

    console.print(
        Panel(
            content,
            title="[bold blue]TheLook eCommerce AI Assistant[/bold blue]",
            border_style="bright_blue",
            padding=(1, 2),
        )
    )


def render_error(
    console: Console,
    title: str,
    message: str,
    resolution_hint: str | None = None,
) -> None:
    """Render high-visibility error panel with actionable resolution instructions."""
    body = f"[bold red]{message}[/bold red]"
    if resolution_hint:
        body += f"\n\n[bold yellow]Resolution:[/bold yellow]\n{resolution_hint}"

    console.print(
        Panel(
            body,
            title=f"🛑 [bold red]{title}[/bold red]",
            border_style="red",
            padding=(1, 2),
        )
    )


def render_executive_report(console: Console, report_markdown: str) -> None:
    """Render executive Markdown briefing with high-contrast styling."""
    md = Markdown(report_markdown)
    console.print(
        Panel(
            md,
            title="📑 [bold green]Strategic Executive Briefing[/bold green]",
            border_style="green",
            padding=(1, 2),
        )
    )


def render_telemetry_card(console: Console, telemetry: dict[str, Any]) -> None:
    """Render compact turn FinOps telemetry summary card."""
    total_calls = telemetry.get("total_llm_calls", 0)
    prompt_tok = telemetry.get("prompt_tokens", 0)
    comp_tok = telemetry.get("completion_tokens", 0)
    total_tok = telemetry.get("total_tokens", prompt_tok + comp_tok)
    latency = telemetry.get("cumulative_latency_sec", 0.0)

    # FinOps Status check (2-5 calls budget)
    if 2 <= total_calls <= 5:
        budget_badge = "[bold green]PASS (Budget 2-5)[/bold green]"
    elif total_calls <= 1:
        budget_badge = "[dim]N/A (Deterministic Turn)[/dim]"
    else:
        budget_badge = "[bold red]EXCEEDED (Max 5)[/bold red]"

    table = Table(
        title="⚡ Execution Telemetry & FinOps Card",
        show_header=True,
        header_style="bold yellow",
        border_style="dim",
        expand=True,
    )
    table.add_column("Turn Latency", justify="center")
    table.add_column("Total Tokens", justify="center")
    table.add_column("Prompt / Completion", justify="center")
    table.add_column("LLM Invocations", justify="center")
    table.add_column("FinOps Discipline", justify="center")

    table.add_row(
        f"{latency:.2f}s",
        f"{total_tok:,}",
        f"{prompt_tok:,} / {comp_tok:,}",
        f"{total_calls} calls",
        budget_badge,
    )

    console.print(table)


def render_hitl_warning(console: Console, prompt_message: str) -> None:
    """Render high-stakes EU AI Act Article 14 human oversight warning panel."""
    console.print(
        Panel(
            f"[bold yellow]{prompt_message}[/bold yellow]",
            title="⚠️ [bold yellow]High-Stakes Oversight (EU AI Act Art. 14)[/bold yellow]",
            border_style="yellow",
            padding=(1, 2),
        )
    )
