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
EXPECTED_VERSION = 2


def _ensure_dir() -> None:
    DB_DIR.mkdir(parents=True, exist_ok=True)


def _create_tables(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
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
        CREATE TABLE IF NOT EXISTS test_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            status TEXT NOT NULL DEFAULT 'pending',
            deck_list TEXT NOT NULL,
            agent_config TEXT NOT NULL,
            batch_size INTEGER DEFAULT 10,
            max_budget REAL,
            created_by INTEGER NOT NULL REFERENCES users(id),
            created_at TEXT DEFAULT (datetime('now')),
            completed_at TEXT
        );
        CREATE TABLE IF NOT EXISTS test_games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL REFERENCES test_tasks(id),
            seed INTEGER NOT NULL,
            p1_agent TEXT NOT NULL,
            p2_agent TEXT NOT NULL,
            deck TEXT NOT NULL,
            steps INTEGER DEFAULT 0,
            winner TEXT,
            token_usage TEXT,
            error_signature TEXT,
            replay_path TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS detected_issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id INTEGER NOT NULL REFERENCES test_games(id),
            task_id INTEGER NOT NULL REFERENCES test_tasks(id),
            severity TEXT NOT NULL DEFAULT 'suspicious',
            category TEXT,
            error_signature TEXT,
            fingerprint_hash TEXT NOT NULL,
            state_snapshot TEXT,
            last_n_actions TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            marked_by INTEGER REFERENCES users(id),
            marked_at TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS cost_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id INTEGER NOT NULL REFERENCES test_games(id),
            model TEXT NOT NULL,
            prompt_tokens INTEGER DEFAULT 0,
            completion_tokens INTEGER DEFAULT 0,
            total_cost REAL DEFAULT 0.0,
            created_at TEXT DEFAULT (datetime('now'))
        );
    """)


def _run_migrations(conn: sqlite3.Connection) -> None:
    current = conn.execute("PRAGMA user_version").fetchone()[0]
    if current < 1:
        _create_tables(conn)
    if current < 2:
        # V1 → V2: add is_admin column and test infrastructure tables
        try:
            conn.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass  # Column already exists
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS test_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                status TEXT NOT NULL DEFAULT 'pending',
                deck_list TEXT NOT NULL,
                agent_config TEXT NOT NULL,
                batch_size INTEGER DEFAULT 10,
                max_budget REAL,
                created_by INTEGER NOT NULL REFERENCES users(id),
                created_at TEXT DEFAULT (datetime('now')),
                completed_at TEXT
            );
            CREATE TABLE IF NOT EXISTS test_games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL REFERENCES test_tasks(id),
                seed INTEGER NOT NULL,
                p1_agent TEXT NOT NULL,
                p2_agent TEXT NOT NULL,
                deck TEXT NOT NULL,
                steps INTEGER DEFAULT 0,
                winner TEXT,
                token_usage TEXT,
                error_signature TEXT,
                replay_path TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS detected_issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id INTEGER NOT NULL REFERENCES test_games(id),
                task_id INTEGER NOT NULL REFERENCES test_tasks(id),
                severity TEXT NOT NULL DEFAULT 'suspicious',
                category TEXT,
                error_signature TEXT,
                fingerprint_hash TEXT NOT NULL,
                state_snapshot TEXT,
                last_n_actions TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                marked_by INTEGER REFERENCES users(id),
                marked_at TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS cost_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id INTEGER NOT NULL REFERENCES test_games(id),
                model TEXT NOT NULL,
                prompt_tokens INTEGER DEFAULT 0,
                completion_tokens INTEGER DEFAULT 0,
                total_cost REAL DEFAULT 0.0,
                created_at TEXT DEFAULT (datetime('now'))
            );
        """)
    conn.execute(f"PRAGMA user_version = {EXPECTED_VERSION}")


def init_db() -> sqlite3.Connection:
    _ensure_dir()
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    _run_migrations(conn)
    conn.commit()
    return conn


def get_db() -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
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
