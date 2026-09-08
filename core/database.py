# core/database.py
import sqlite3
from datetime import datetime

DB_NAME = "nexus_sms.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            sender TEXT,
            category TEXT,
            extracted_code TEXT,
            raw_body TEXT
        )
    """)
    conn.commit()
    conn.close()

def log_message(sender: str, category: str, extracted_code: str, raw_body: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    timestamp = datetime.utcnow().isoformat()
    cursor.execute("""
        INSERT INTO messages (timestamp, sender, category, extracted_code, raw_body)
        VALUES (?, ?, ?, ?, ?)
    """, (timestamp, sender, category, extracted_code, raw_body))
    conn.commit()
    conn.close()

def get_recent_messages(limit: int = 10):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, sender, category, extracted_code FROM messages ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows
