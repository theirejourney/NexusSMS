"""SQLite persistence layer with universal provider support."""

from __future__ import annotations

import os
import sqlite3
import json
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator, Optional

DEFAULT_DB = os.environ.get("NEXUSSMS_DB", "nexus_sms.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS messages (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    provider            TEXT NOT NULL DEFAULT 'twilio',
    provider_message_id TEXT NOT NULL,
    timestamp           TEXT NOT NULL,
    sender              TEXT NOT NULL,
    recipient           TEXT,
    category            TEXT,
    extracted_code      TEXT,
    raw_body            TEXT NOT NULL,
    raw_payload         TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_provider_msg_id 
    ON messages(provider, provider_message_id);

CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_messages_sender    ON messages(sender COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS idx_messages_provider  ON messages(provider);
CREATE INDEX IF NOT EXISTS idx_messages_category  ON messages(category);
"""


@contextmanager
def connect(db_path: str = DEFAULT_DB) -> Iterator[sqlite3.Connection]:
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


def is_duplicate(provider: str, provider_message_id: str, db_path: str = DEFAULT_DB) -> bool:
    if not provider_message_id:
        return False
    with connect(db_path) as conn:
        row = conn.execute(
            "SELECT 1 FROM messages WHERE provider = ? AND provider_message_id = ?",
            (provider, provider_message_id)
        ).fetchone()
        return row is not None


def insert_message(unified, result: dict, db_path: str = DEFAULT_DB) -> bool:
    """Insert a normalized message. Returns True if inserted, False if duplicate."""
    from providers.base import UnifiedMessage
    
    if not isinstance(unified, UnifiedMessage):
        raise TypeError("unified must be a UnifiedMessage instance")
    
    with connect(db_path) as conn:
        cur = conn.execute(
            """INSERT OR IGNORE INTO messages
               (provider, provider_message_id, timestamp, sender, recipient,
                category, extracted_code, raw_body, raw_payload)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                unified.provider,
                unified.provider_message_id,
                datetime.now(timezone.utc).isoformat(),
                unified.sender,
                unified.recipient,
                result.get("category", "unknown"),
                result.get("extracted_code"),
                unified.body,
                json.dumps(unified.raw_payload, default=str)
            ),
        )
        return cur.rowcount > 0


def get_messages(
    sender: Optional[str] = None,
    provider: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 20,
    db_path: str = DEFAULT_DB
) -> list[dict]:
    query = "SELECT * FROM messages WHERE 1=1"
    params = []
    
    if sender:
        query += " AND sender LIKE ? COLLATE NOCASE"
        params.append(f"%{sender}%")
    if provider:
        query += " AND provider = ?"
        params.append(provider)
    if category:
        query += " AND category = ?"
        params.append(category)
    
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    
    with connect(db_path) as conn:
        return [dict(r) for r in conn.execute(query, params).fetchall()]


# Backward-compatible aliases
message_exists = is_duplicate


def log_message(sender: str, category: str, extracted_code: Optional[str],
                raw_body: str, message_sid: Optional[str] = None,
                db_path: str = DEFAULT_DB) -> bool:
    """Backward-compatible insert wrapper."""
    from providers.base import UnifiedMessage
    
    unified = UnifiedMessage(
        provider="twilio",
        provider_message_id=message_sid or "",
        sender=sender,
        recipient="",
        body=raw_body,
        timestamp=None,
        raw_payload={}
    )
    return insert_message(unified, {
        "category": category,
        "extracted_code": extracted_code,
    }, db_path)


def get_recent_messages(limit: int = 10, sender: Optional[str] = None,
                        provider: Optional[str] = None,
                        category: Optional[str] = None,
                        db_path: str = DEFAULT_DB) -> list[dict]:
    """Backward-compatible fetch wrapper."""
    return get_messages(
        sender=sender,
        provider=provider,
        category=category,
        limit=limit,
        db_path=db_path
    )


def get_latest_code(sender: Optional[str] = None, category: Optional[str] = None,
                    db_path: str = DEFAULT_DB) -> Optional[str]:
    """Return the most recently extracted code, optionally filtered."""
    rows = get_recent_messages(limit=1, sender=sender, category=category, db_path=db_path)
    return rows[0]["extracted_code"] if rows else None
