"""Persistent Local Storage Module for Reports and Executive Assets.

Operationalizes ADR-0004 (SQLite Local Persistence vs CloudSQL).
"""

from src.storage.reports import (
    delete_report,
    get_report,
    init_db,
    list_reports,
    save_report,
)

__all__ = [
    "delete_report",
    "get_report",
    "init_db",
    "list_reports",
    "save_report",
]
