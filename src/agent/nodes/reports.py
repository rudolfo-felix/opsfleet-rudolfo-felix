"""Executive Reports Management & EU AI Act HITL Oversight Node.

Operationalizes ADR-0004 (SQLite Local Persistence), Invariant 10 (HITL Interrupt & Checkpointer),
and EU AI Act Article 14 (Human Oversight Gate for destructive operations).
"""

import logging
import re
from datetime import datetime
from typing import Any

from langgraph.types import interrupt

from src.agent.state import AgentState
from src.storage.reports import (
    delete_report,
    get_report,
    list_reports,
    save_report,
)

logger = logging.getLogger(__name__)


def _extract_report_id(query: str) -> int | None:
    """Extract report integer ID from user input (e.g., 'delete report #3' or 'remove report 4')."""
    match = re.search(r"\b(?:report\s*#?\s*|#)(\d+)\b", query, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def _extract_search_keyword(query: str) -> str | None:
    """Extract optional search keyword from listing queries."""
    clean = re.sub(
        r"^\s*(?:show|list|view|search|find)\s+(?:saved\s+)?reports?\s*",
        "",
        query,
        flags=re.IGNORECASE,
    ).strip()
    clean = re.sub(r"^(?:for|matching|with|about)\s+", "", clean, flags=re.IGNORECASE).strip()
    return clean if clean else None


def _extract_save_title(query: str, fallback_query: str) -> str:
    """Extract custom title from save command or construct a clean default title."""
    match = re.search(
        r"\b(?:save|bookmark|store)\s+report\s+(?:as|titled|named)?\s*(.+)$",
        query,
        re.IGNORECASE,
    )
    if match:
        custom_title = match.group(1).strip().strip("'\"")
        if custom_title:
            return custom_title

    # Construct clean default title with timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    clean_topic = fallback_query.strip().rstrip("?.") if fallback_query else "Retail Analysis"
    return f"{clean_topic} ({timestamp})"


def format_reports_table(reports: list[dict[str, Any]]) -> str:
    """Format list of saved reports as a readable markdown table."""
    if not reports:
        return (
            "📂 **No Saved Reports:** No reports found matching your request.\n"
            "Run an analytical query and type *'save report'* to preserve a strategic briefing."
        )

    lines = [
        "## 📑 Saved Executive Reports\n",
        "| ID | Created | Title | Tags |",
        "|:---:|:---:|---|---|",
    ]

    for r in reports:
        r_id = f"#{r['id']}"
        created = r["created_at"][:16] if r.get("created_at") else "N/A"
        title = r["title"]
        tags = ", ".join(r.get("tags") or []) or "—"
        lines.append(f"| {r_id} | {created} | {title} | {tags} |")

    lines.append("\n*To view full report details, ask: 'view report #ID'. To delete: 'delete report #ID'.*")
    return "\n".join(lines)


def reports_node(state: AgentState) -> dict[str, Any]:
    """LangGraph node: manage report lifecycle with EU AI Act Article 14 HITL oversight."""
    user_query = state.get("user_query", "").strip()
    user_id = state.get("user_id", "executive_user")
    current_report = state.get("executive_report")

    # --------------------------------------------------------------------------
    # 1. DESTRUCTIVE DELETION FLOW (EU AI Act Article 14 Human Oversight Gate)
    # --------------------------------------------------------------------------
    if re.search(r"\b(delete|remove|clear|drop|purge)\b", user_query, re.IGNORECASE):
        report_id = _extract_report_id(user_query)

        if report_id is None:
            return {
                "requires_confirmation": False,
                "executive_report": (
                    "⚠️ **Missing Report ID:** Please specify the report number to delete.\n"
                    "Example: *'delete report #2'* or *'remove report 5'*."
                ),
            }

        existing_report = get_report(report_id)
        if not existing_report:
            return {
                "requires_confirmation": False,
                "executive_report": f"⚠️ **Report Not Found:** Report #{report_id} does not exist in local storage.",
            }

        title = existing_report["title"]
        prompt_message = (
            f"⚠️ **High-Stakes Oversight (EU AI Act Art. 14):** Are you sure you want to delete "
            f"report #{report_id} ('{title}')? This operation cannot be undone. [y/N]: "
        )

        # Pause graph execution via LangGraph interrupt()
        human_decision = interrupt(
            {
                "action": "delete_report",
                "report_id": report_id,
                "title": title,
                "prompt": prompt_message,
            }
        )

        # Evaluate confirmation strictly with default-deny principle
        is_confirmed = str(human_decision).strip().lower() in ("y", "yes", "true", "1")

        if is_confirmed:
            deleted = delete_report(report_id)
            if deleted:
                msg = f"🗑️ **Report Deleted:** Report #{report_id} ('{title}') has been permanently deleted from storage."
            else:
                msg = f"⚠️ Report #{report_id} could not be deleted."

            return {
                "requires_confirmation": False,
                "confirmation_status": True,
                "executive_report": msg,
            }
        else:
            return {
                "requires_confirmation": False,
                "confirmation_status": False,
                "executive_report": (
                    f"🛑 **Action Cancelled:** Deletion of report #{report_id} ('{title}') was aborted by user. "
                    "Data remains completely intact."
                ),
            }

    # --------------------------------------------------------------------------
    # 2. SAVE REPORT FLOW
    # --------------------------------------------------------------------------
    if re.search(r"\b(save|bookmark|store)\b", user_query, re.IGNORECASE):
        if not current_report or not current_report.strip():
            return {
                "requires_confirmation": False,
                "executive_report": (
                    "⚠️ **No Active Report:** There is no synthesized executive report in the current session to save.\n"
                    "Run an analytical question first (e.g. *'What was Net Revenue by category?'*), then type *'save report'*."
                ),
            }

        title = _extract_save_title(user_query, state.get("user_query", "Executive Briefing"))
        report_id = save_report(
            user_id=user_id,
            title=title,
            content=current_report,
            tags=["executive", "briefing"],
        )

        return {
            "requires_confirmation": False,
            "executive_report": (
                f"💾 **Report Saved Successfully:** Saved as **Report #{report_id}** ('{title}').\n"
                "You can inspect saved reports at any time with *'show saved reports'*."
            ),
        }

    # --------------------------------------------------------------------------
    # 3. LIST / SEARCH REPORTS FLOW
    # --------------------------------------------------------------------------
    keyword = _extract_search_keyword(user_query)
    reports = list_reports(user_id=None, keyword=keyword)  # Display reports for all active personas in CLI
    table_markdown = format_reports_table(reports)

    return {
        "requires_confirmation": False,
        "executive_report": table_markdown,
    }
