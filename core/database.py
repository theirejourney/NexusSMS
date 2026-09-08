"""SQLite persistence layer with idempotency, context managers and indexes."""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator, Optional

DEFAULT_DB = os.environ.get("NEXUSSMS_DB", "nexus_sms.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS messages (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    message_sid   TEXT UNIQUE,              -- Twilio MessageSid: dedupe retries
    timestamp     TEXT NOT NULL,
    sender        TEXT NOT NULL,
    category      TEXT NOT NULL,
    extracted_code TEXT,
    raw_body      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_messages_sender    ON messages(sender);
CREATE INDEX IF NOT EXISTS idx_messages_code      ON messages(extracted_code);
"""


@contextmanager
def connect(db_path: str = DEFAULT_DB) -> Iterator[sqlite3.Connection]:
    """Yield a connection with WAL mode, foreign keys and safe cleanup."""
    conn = sqlite3.connect(db_path, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: str = DEFAULT_DB) -> None:
    with connect(db_path) as conn:
        conn.executescript(_SCHEMA)


def message_exists(message_sid: str, db_path: str = DEFAULT_DB) -> bool:
    if not message_sid:
        return False
    with connect(db_path) as conn:
        row = conn.execute("SELECT 1 FROM messages WHERE message_sid = ?",
                           (message_sid,)).fetchone()
        return row is not None


def log_message(sender: str, category: str, extracted_code: Optional[str],
                raw_body: str, message_sid: Optional[str] = None,
                db_path: str = DEFAULT_DB) -> bool:
    """Insert a message. Returns False (no-op) if message_sid already exists."""
    init_db(db_path)
    with connect(db_path) as conn:
        cur = conn.execute(
            """INSERT OR IGNORE INTO messages
               (message_sid, timestamp, sender, category, extracted_code, raw_body)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (message_sid, datetime.now(timezone.utc).isoformat(),
             sender, category, extracted_code, raw_body),
        )
        return cur.rowcount > 0


def get_recent_messages(limit: int = 10, sender: Optional[str] = None,
                        category: Optional[str] = None,
                        db_path: str = DEFAULT_DB) -> list[dict]:
    """Fetch recent messages, optionally filtered by sender and/or category."""
    query, params = "SELECT * FROM messages WHERE 1=1", []
    if sender:
        query += " AND sender LIKE ?"
        params.append(f"%{sender}%")
    if category:
        query += " AND category = ?"
        params.append(category)
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    with connect(db_path) as conn:
        return [dict(r) for r in conn.execute(query, params).fetchall()]


def get_latest_code(sender: Optional[str] = None, category: Optional[str] = None,
                    db_path: str = DEFAULT_DB) -> Optional[str]:
    """Return the most recently extracted code, optionally filtered."""
    rows = get_recent_messages(limit=1, sender=sender, category=category, db_path=db_path)
    return rows[0]["extracted_code"] if rows else None
