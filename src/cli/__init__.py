"""Rich CLI module for TheLook Retail Assistant.

Operationalizes Invariant 1 (2-Minute Evaluator Rule) and Invariant 10 (HITL Interrupt).
"""

from src.cli.tables import format_records_to_table
from src.cli.view import (
    render_banner,
    render_error,
    render_executive_report,
    render_hitl_warning,
    render_telemetry_card,
)

__all__ = [
    "format_records_to_table",
    "render_banner",
    "render_error",
    "render_executive_report",
    "render_hitl_warning",
    "render_telemetry_card",
]
