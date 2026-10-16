"""Persistent Local SQLite Storage Engine for Executive Briefings.

Operationalizes ADR-0004 (SQLite Local Persistence vs CloudSQL) and Invariant 1 (2-minute rule).
Provides zero-configuration relational storage with full CRUD and case-insensitive keyword search.
"""

import json
import logging
import sqlite3
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from src.config import get_settings

logger = logging.getLogger(__name__)


def _resolve_db_path(db_path: str | Path | None = None) -> Path:
    """Resolve database path, falling back to application settings and ensuring parent directories exist."""
    if db_path is not None:
        target = Path(db_path)
    else:
        try:
            target = Path(get_settings().storage_db_path)
        except Exception:
            target = Path("reports.db")

    if target.parent and not target.parent.exists():
        target.parent.mkdir(parents=True, exist_ok=True)

    return target


def get_connection(db_path: str | Path | None = None) -> sqlite3.Connection:
    """Open an SQLite connection configured with row dictionary mapping."""
    path = _resolve_db_path(db_path)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str | Path | None = None) -> None:
    """Initialize SQLite reports table schema and indexes if not already present."""
    path = _resolve_db_path(db_path)
    logger.debug(f"Initializing reports database at {path}")

    with get_connection(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tags TEXT
            );
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_reports_user_id ON reports(user_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports(created_at);")
        conn.commit()


def save_report(
    user_id: str,
    title: str,
    content: str,
    tags: Sequence[str] | str | None = None,
    db_path: str | Path | None = None,
) -> int:
    """Persist an executive report briefing and return its unique identifier."""
    init_db(db_path)

    # Serialize tags into JSON string for SQLite storage
    tags_json = None
    if tags is not None:
        if isinstance(tags, str):
            tags_json = json.dumps([t.strip() for t in tags.split(",") if t.strip()])
        else:
            tags_json = json.dumps(list(tags))

    with get_connection(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO reports (user_id, title, content, tags)
            VALUES (?, ?, ?, ?);
            """,
            (user_id, title.strip(), content.strip(), tags_json),
        )
        conn.commit()
        report_id = cursor.lastrowid
        logger.info(f"Saved executive report #{report_id}: '{title}' for user '{user_id}'.")
        return int(report_id)


def _deserialize_tags(tags_raw: str | None) -> list[str]:
    """Safely deserialize JSON tags string into list of strings."""
    if not tags_raw:
        return []
    try:
        val = json.loads(tags_raw)
        return list(val) if isinstance(val, list) else [str(val)]
    except Exception:
        return [t.strip() for t in tags_raw.split(",") if t.strip()]


def list_reports(
    user_id: str | None = None,
    keyword: str | None = None,
    db_path: str | Path | None = None,
) -> list[dict[str, Any]]:
    """List saved reports with optional user filtering and case-insensitive keyword search."""
    init_db(db_path)

    query = "SELECT id, user_id, title, content, created_at, tags FROM reports"
    clauses: list[str] = []
    params: list[Any] = []

    if user_id:
        clauses.append("user_id = ?")
        params.append(user_id)

    if keyword and keyword.strip():
        search_pattern = f"%{keyword.strip().lower()}%"
        clauses.append("(LOWER(title) LIKE ? OR LOWER(content) LIKE ?)")
        params.extend([search_pattern, search_pattern])

    if clauses:
        query += " WHERE " + " AND ".join(clauses)

    query += " ORDER BY created_at DESC, id DESC;"

    with get_connection(db_path) as conn:
        rows = conn.execute(query, params).fetchall()

    results: list[dict[str, Any]] = []
    for row in rows:
        results.append(
            {
                "id": row["id"],
                "user_id": row["user_id"],
                "title": row["title"],
                "content": row["content"],
                "created_at": str(row["created_at"]),
                "tags": _deserialize_tags(row["tags"]),
            }
        )

    return results


def get_report(
    report_id: int,
    db_path: str | Path | None = None,
) -> dict[str, Any] | None:
    """Retrieve a single saved report by its unique ID."""
    init_db(db_path)

    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT id, user_id, title, content, created_at, tags FROM reports WHERE id = ?;",
            (report_id,),
        ).fetchone()

    if not row:
        return None

    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "title": row["title"],
        "content": row["content"],
        "created_at": str(row["created_at"]),
        "tags": _deserialize_tags(row["tags"]),
    }


def delete_report(
    report_id: int,
    db_path: str | Path | None = None,
) -> bool:
    """Delete a report by its unique ID. Returns True if deleted, False if not found."""
    init_db(db_path)

    with get_connection(db_path) as conn:
        cursor = conn.execute(
            "DELETE FROM reports WHERE id = ?;",
            (report_id,),
        )
        conn.commit()
        deleted = cursor.rowcount > 0
        if deleted:
            logger.info(f"Deleted report #{report_id} from SQLite storage.")
        else:
            logger.warning(f"Attempted to delete non-existent report #{report_id}.")
        return deleted
