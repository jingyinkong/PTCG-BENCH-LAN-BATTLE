"""
Match record API for retrieving player battle history and stats.
"""

import sqlite3
from typing import Optional

from fastapi import APIRouter, Depends, Query

from auth import get_current_user
from database import DB_PATH

router = APIRouter(prefix="/api/match-records", tags=["match-records"])


@router.get("")
def list_records(
    user: dict = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> dict:
    db = sqlite3.connect(str(DB_PATH))
    db.row_factory = sqlite3.Row
    try:
        rows = db.execute(
            """SELECT m.*, 
               p1.username as player1_name, p2.username as player2_name,
               w.username as winner_name
            FROM match_records m
            LEFT JOIN users p1 ON m.player1_user_id = p1.id
            LEFT JOIN users p2 ON m.player2_user_id = p2.id
            LEFT JOIN users w ON m.winner_user_id = w.id
            WHERE m.player1_user_id = ? OR m.player2_user_id = ?
            ORDER BY m.played_at DESC
            LIMIT ? OFFSET ?""",
            (user["id"], user["id"], limit, offset)
        ).fetchall()
        return {"records": [dict(r) for r in rows]}
    finally:
        db.close()


@router.get("/stats")
def get_stats(user: dict = Depends(get_current_user)) -> dict:
    db = sqlite3.connect(str(DB_PATH))
    db.row_factory = sqlite3.Row
    try:
        total = db.execute(
            "SELECT COUNT(*) as cnt FROM match_records WHERE player1_user_id = ? OR player2_user_id = ?",
            (user["id"], user["id"])
        ).fetchone()["cnt"]

        wins = db.execute(
            "SELECT COUNT(*) as cnt FROM match_records WHERE winner_user_id = ?",
            (user["id"],)
        ).fetchone()["cnt"]

        favorite = db.execute(
            """SELECT deck1_name as deck, COUNT(*) as cnt FROM match_records 
            WHERE player1_user_id = ? AND deck1_name IS NOT NULL
            GROUP BY deck1_name
            UNION ALL
            SELECT deck2_name as deck, COUNT(*) as cnt FROM match_records
            WHERE player2_user_id = ? AND deck2_name IS NOT NULL
            GROUP BY deck2_name
            ORDER BY cnt DESC LIMIT 3""",
            (user["id"], user["id"])
        ).fetchall()

        return {
            "total_games": total,
            "wins": wins,
            "losses": total - wins,
            "win_rate": round(wins / total, 3) if total > 0 else 0.0,
            "favorite_decks": [dict(r) for r in favorite],
        }
    finally:
        db.close()
