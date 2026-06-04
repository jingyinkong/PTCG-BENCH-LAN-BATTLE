"""
SQLite database initialization and connection management for PTCG-Bench.

Provides:
- WAL-mode SQLite database at backend/data/ptcg.db
- Schema creation with PRAGMA user_version-based migration
- get_db() FastAPI dependency returning a sqlite3.Row connection
"""

import sqlite3
from pathlib import Path
from typing import Generator

DB_DIR = Path(__file__).parent / "data"
DB_PATH = DB_DIR / "ptcg.db"
EXPECTED_VERSION = 1


def _ensure_dir() -> None:
    DB_DIR.mkdir(parents=True, exist_ok=True)


def _create_tables(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            token TEXT UNIQUE NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS match_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_room_id TEXT NOT NULL,
            player1_user_id INTEGER NOT NULL REFERENCES users(id),
            player2_user_id INTEGER NOT NULL REFERENCES users(id),
            winner_user_id INTEGER REFERENCES users(id),
            loser_user_id INTEGER REFERENCES users(id),
            deck1_name TEXT,
            deck2_name TEXT,
            total_turns INTEGER,
            duration_seconds REAL,
            played_at TEXT DEFAULT (datetime('now'))
        );
    """)


def _run_migrations(conn: sqlite3.Connection) -> None:
    current = conn.execute("PRAGMA user_version").fetchone()[0]
    if current < 1:
        _create_tables(conn)
    conn.execute(f"PRAGMA user_version = {EXPECTED_VERSION}")


def init_db() -> sqlite3.Connection:
    _ensure_dir()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    _run_migrations(conn)
    conn.commit()
    return conn


def get_db() -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


_init_conn = None
try:
    _init_conn = init_db()
finally:
    if _init_conn:
        _init_conn.close()
