"""Persistent saved-designs store backed by SQLite.

Replaces the previous in-memory list (_local_saved) so designs survive
server restarts, Docker container rebuilds, and EC2 reboots.

Schema
------
designs (
    id          TEXT PRIMARY KEY,   -- e.g. "vel-123456"
    data        TEXT NOT NULL,      -- full FinalDesignPackage as JSON
    created_at  TEXT NOT NULL       -- ISO-8601 UTC timestamp
)

The entire design payload is stored as a single JSON blob. This avoids
having to maintain a column-per-field schema as the frontend evolves —
any new fields land in the blob automatically.
"""

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, HTTPException

# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------

DB_PATH = os.getenv("VELARIS_DB_PATH", "velaris.db")


def _abs_db_path() -> str:
    p = DB_PATH
    if not os.path.isabs(p):
        p = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), p))
    return p


def _get_connection() -> sqlite3.Connection:
    # timeout=30s + WAL: concurrent writers wait instead of raising
    # "database is locked" (SQLite default timeout is only 5s).
    conn = sqlite3.connect(_abs_db_path(), check_same_thread=False, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")   # safe for concurrent reads
    conn.execute("PRAGMA busy_timeout=30000")  # belt-and-braces writer wait
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def _db():
    conn = _get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Create the designs table if it doesn't exist. Called once at startup."""
    with _db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS designs (
                id         TEXT PRIMARY KEY,
                data       TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)


# init_db() is called from main.py startup event, not on import.


# ---------------------------------------------------------------------------
# Core helpers (used by other modules, e.g. pdf_generator)
# ---------------------------------------------------------------------------

def get_design_by_id(design_id: str) -> Optional[Dict[str, Any]]:
    """Return a single design dict, or None if not found."""
    with _db() as conn:
        row = conn.execute(
            "SELECT data FROM designs WHERE id = ?", (design_id,)
        ).fetchone()
    return json.loads(row["data"]) if row else None


def get_all_designs() -> List[Dict[str, Any]]:
    """Return all saved designs, newest first."""
    with _db() as conn:
        rows = conn.execute(
            "SELECT data FROM designs ORDER BY created_at DESC"
        ).fetchall()
    return [json.loads(r["data"]) for r in rows]


def upsert_design(design: Dict[str, Any]) -> str:
    """Insert or replace a design. Returns the design id."""
    design_id = design.get("id") or f"vel-{__import__('random').randint(100000, 999999)}"
    design["id"] = design_id
    now = datetime.now(timezone.utc).isoformat()

    with _db() as conn:
        conn.execute(
            """
            INSERT INTO designs (id, data, created_at)
            VALUES (?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                data       = excluded.data,
                created_at = excluded.created_at
            """,
            (design_id, json.dumps(design), now),
        )
    return design_id


def delete_design(design_id: str) -> bool:
    """Delete a design by id. Returns True if a row was removed."""
    with _db() as conn:
        cursor = conn.execute(
            "DELETE FROM designs WHERE id = ?", (design_id,)
        )
    return cursor.rowcount > 0


def clear_all_designs() -> None:
    """Wipe every saved design (used in tests)."""
    with _db() as conn:
        conn.execute("DELETE FROM designs")


def design_count() -> int:
    """Return total number of saved designs."""
    with _db() as conn:
        row = conn.execute("SELECT COUNT(*) AS n FROM designs").fetchone()
    return row["n"]


# ---------------------------------------------------------------------------
# FastAPI router 
# ---------------------------------------------------------------------------

router = APIRouter()


MAX_DESIGN_BYTES = 2_000_000

@router.post("/api/save-design")
def save_design(design: dict = Body(...)) -> dict:
    blob = json.dumps(design)
    if len(blob.encode("utf-8")) > MAX_DESIGN_BYTES:
        raise HTTPException(status_code=413, detail="Design payload too large")
    if design.get("inputImage") and len(str(design["inputImage"])) > MAX_DESIGN_BYTES:
        raise HTTPException(status_code=413, detail="inputImage too large")
    design_id = upsert_design(design)
    return {"success": True, "id": design_id, "totalCount": design_count()}


@router.get("/api/saved-designs")
def get_saved_designs(limit: int = 50, offset: int = 0) -> List[dict]:
    limit = max(1, min(limit, 100))
    offset = max(0, offset)
    with _db() as conn:
        rows = conn.execute(
            "SELECT data FROM designs ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
    return [json.loads(r["data"]) for r in rows]


@router.delete("/api/saved-designs/{design_id}")
def delete_saved_design(design_id: str) -> dict:
    removed = delete_design(design_id)
    if not removed:
        raise HTTPException(status_code=404, detail=f"Design '{design_id}' not found")
    return {"success": True, "id": design_id}
