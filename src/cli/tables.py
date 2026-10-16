"""Rich Table Formatter for Retail Data Analysis Assistant.

Converts tabular records and DataFrames into formatted terminal tables
with automatic truncation, column styling, and alternating row highlights.
"""

from typing import Any

from rich.table import Table


def format_records_to_table(
    records: list[dict[str, Any]],
    title: str = "📊 Data Warehouse Output",
    max_rows: int = 15,
) -> Table:
    """Convert list of row dictionaries into a stylized Rich Table."""
    table = Table(
        title=title,
        show_header=True,
        header_style="bold cyan",
        border_style="blue",
        row_styles=["none", "dim"],
    )

    if not records:
        table.add_column("Notice", justify="center")
        table.add_row("Zero records returned from data warehouse.")
        return table

    # Collect headers from first record
    headers = list(records[0].keys())
    for header in headers:
        # Determine alignment based on column name hints
        justify = "right" if any(
            k in header.lower()
            for k in ("id", "count", "num", "revenue", "price", "margin", "cost", "sale", "pct", "rate")
        ) else "left"
        table.add_column(str(header), justify=justify, style="white")

    # Add rows with truncation
    display_records = records[:max_rows]
    for row in display_records:
        formatted_row: list[str] = []
        for header in headers:
            val = row.get(header)
            if val is None:
                formatted_row.append("—")
            elif isinstance(val, float):
                formatted_row.append(f"{val:,.2f}")
            elif isinstance(val, int):
                formatted_row.append(f"{val:,}")
            else:
                formatted_row.append(str(val))
        table.add_row(*formatted_row)

    if len(records) > max_rows:
        table.caption = f"[dim italic]Showing top {max_rows} of {len(records)} total records[/dim italic]"

    return table
