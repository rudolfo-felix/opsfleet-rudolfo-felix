"""Tests for SQLite Storage & EU AI Act HITL Interrupt Governance (OPS-007).

Validates:
1. SQLite storage engine CRUD operations and case-insensitive keyword search.
2. LangGraph HITL interrupt() pattern using MemorySaver checkpointer.
3. User confirmation branch committing permanent deletion.
4. User cancellation branch aborting deletion and preserving data integrity.
5. Missing and non-existent report ID edge cases.
"""

import uuid
from pathlib import Path

import pytest
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from src.agent.graph import create_retail_agent_graph
from src.agent.nodes.reports import reports_node
from src.agent.state import create_initial_state
from src.config import get_settings
from src.storage.reports import (
    delete_report,
    get_report,
    init_db,
    list_reports,
    save_report,
)


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Isolate each test with a clean temporary SQLite database."""
    test_db = tmp_path / f"test_reports_{uuid.uuid4().hex[:8]}.db"
    monkeypatch.setenv("STORAGE_DB_PATH", str(test_db))
    get_settings.cache_clear()
    init_db(test_db)
    yield test_db
    get_settings.cache_clear()


def test_sqlite_storage_crud_and_search(setup_test_db: Path):
    """Verify SQLite CRUD lifecycle and case-insensitive keyword search."""
    db = setup_test_db

    # 1. Save reports
    id1 = save_report(
        user_id="exec_sarah",
        title="Q1 2026 Margin Analysis",
        content="## Executive Summary\nGross margins in Denim reached 42.5%.",
        tags=["margins", "denim", "q1"],
        db_path=db,
    )
    assert id1 > 0

    id2 = save_report(
        user_id="exec_marcus",
        title="Activewear Churn Deep Dive",
        content="## Key Findings\nCustomer churn in Activewear spiked by 3.2%.",
        tags="churn,activewear",
        db_path=db,
    )
    assert id2 > id1

    # 2. Retrieve single report
    rep1 = get_report(id1, db_path=db)
    assert rep1 is not None
    assert rep1["title"] == "Q1 2026 Margin Analysis"
    assert "42.5%" in rep1["content"]
    assert "margins" in rep1["tags"]

    # 3. List all reports
    all_reports = list_reports(db_path=db)
    assert len(all_reports) == 2

    # 4. Filter by user_id
    sarah_reports = list_reports(user_id="exec_sarah", db_path=db)
    assert len(sarah_reports) == 1
    assert sarah_reports[0]["id"] == id1

    # 5. Case-insensitive keyword search on title and content
    margin_search = list_reports(keyword="mArGiN", db_path=db)
    assert len(margin_search) == 1
    assert margin_search[0]["id"] == id1

    activewear_search = list_reports(keyword="activewear", db_path=db)
    assert len(activewear_search) == 1
    assert activewear_search[0]["id"] == id2

    # 6. Delete report
    deleted = delete_report(id1, db_path=db)
    assert deleted is True
    assert get_report(id1, db_path=db) is None
    assert len(list_reports(db_path=db)) == 1

    # 7. Delete non-existent report
    assert delete_report(9999, db_path=db) is False


def test_hitl_interrupt_and_confirm_deletion(setup_test_db: Path):
    """Verify EU AI Act Article 14 HITL interrupt on destructive deletion when user confirms."""
    db = setup_test_db
    rep_id = save_report(
        user_id="exec_user",
        title="Crucial Strategic Briefing",
        content="Sensitive analysis to be deleted",
        tags=["strategic"],
        db_path=db,
    )

    checkpointer = MemorySaver()
    graph = create_retail_agent_graph(checkpointer=checkpointer)
    thread_id = f"test-thread-{uuid.uuid4().hex[:6]}"
    config = {"configurable": {"thread_id": thread_id}}

    # 1. Trigger deletion command -> must pause execution at interrupt()
    initial_state = create_initial_state(f"Delete report #{rep_id}", user_id="exec_user")
    paused_result = graph.invoke(initial_state, config=config)

    assert "__interrupt__" in paused_result
    interrupt_payload = paused_result["__interrupt__"][0].value
    assert interrupt_payload["action"] == "delete_report"
    assert interrupt_payload["report_id"] == rep_id
    assert "Crucial Strategic Briefing" in interrupt_payload["title"]
    assert "High-Stakes Oversight" in interrupt_payload["prompt"]

    # Verify report is still present before confirmation
    assert get_report(rep_id, db_path=db) is not None

    # 2. Resume execution with human confirmation ('yes')
    resumed_result = graph.invoke(Command(resume="yes"), config=config)

    assert resumed_result["confirmation_status"] is True
    assert "permanently deleted" in resumed_result["executive_report"]

    # Verify report is permanently deleted from SQLite
    assert get_report(rep_id, db_path=db) is None


def test_hitl_interrupt_and_abort_deletion(setup_test_db: Path):
    """Verify EU AI Act Article 14 HITL interrupt aborts when user denies confirmation."""
    db = setup_test_db
    rep_id = save_report(
        user_id="exec_user",
        title="Vital Financial Audit",
        content="Do not delete this report under any circumstance",
        tags=["vital"],
        db_path=db,
    )

    checkpointer = MemorySaver()
    graph = create_retail_agent_graph(checkpointer=checkpointer)
    thread_id = f"test-thread-{uuid.uuid4().hex[:6]}"
    config = {"configurable": {"thread_id": thread_id}}

    # 1. Trigger deletion command -> must pause at interrupt()
    initial_state = create_initial_state(f"remove report {rep_id}", user_id="exec_user")
    paused_result = graph.invoke(initial_state, config=config)
    assert "__interrupt__" in paused_result

    # 2. Resume execution with human cancellation ('no')
    resumed_result = graph.invoke(Command(resume="no"), config=config)

    assert resumed_result["confirmation_status"] is False
    assert "Action Cancelled" in resumed_result["executive_report"]
    assert "Data remains completely intact" in resumed_result["executive_report"]

    # Verify report is STILL present in storage
    preserved = get_report(rep_id, db_path=db)
    assert preserved is not None
    assert preserved["title"] == "Vital Financial Audit"


def test_delete_missing_id_and_non_existent():
    """Verify error guidance when report ID is missing or non-existent without pausing."""
    # 1. Missing ID
    state_missing = create_initial_state("Please delete report")
    result_missing = reports_node(state_missing)
    assert "Missing Report ID" in result_missing["executive_report"]
    assert result_missing["requires_confirmation"] is False

    # 2. Non-existent ID
    state_not_found = create_initial_state("Delete report #999999")
    result_not_found = reports_node(state_not_found)
    assert "Report Not Found" in result_not_found["executive_report"]
    assert result_not_found["requires_confirmation"] is False


def test_save_and_list_reports_flow(setup_test_db: Path):
    """Verify save report node flow and list reports formatting."""
    db = setup_test_db

    # 1. Attempt save when no report exists
    state_empty = create_initial_state("save report")
    state_empty["executive_report"] = None
    res_empty = reports_node(state_empty)
    assert "No Active Report" in res_empty["executive_report"]

    # 2. Save active report
    state_save = create_initial_state("save report as Q3 Footwear Summary")
    state_save["executive_report"] = "## Executive Summary\nFootwear grew 15%."
    res_save = reports_node(state_save)
    assert "Report Saved Successfully" in res_save["executive_report"]
    assert "Q3 Footwear Summary" in res_save["executive_report"]

    # Verify saved in SQLite
    saved_items = list_reports(db_path=db)
    assert len(saved_items) == 1
    assert saved_items[0]["title"] == "Q3 Footwear Summary"

    # 3. List saved reports
    state_list = create_initial_state("show saved reports")
    res_list = reports_node(state_list)
    assert "## 📑 Saved Executive Reports" in res_list["executive_report"]
    assert "Q3 Footwear Summary" in res_list["executive_report"]
