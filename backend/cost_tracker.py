"""Cost tracking API for AI battle testing."""

import sqlite3
from fastapi import APIRouter, Depends, HTTPException, Query
from auth import get_current_user
from database import get_db

router = APIRouter(prefix="/api/test", tags=["cost"])


def _require_admin(user: dict) -> None:
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")


@router.get("/cost")
def get_task_cost(task_id: int = Query(...), user: dict = Depends(get_current_user),
                  db: sqlite3.Connection = Depends(get_db)):
    _require_admin(user)
    rows = db.execute(
        "SELECT model, SUM(prompt_tokens) as pt, SUM(completion_tokens) as ct, "
        "SUM(total_cost) as tc FROM cost_records "
        "WHERE game_id IN (SELECT id FROM test_games WHERE task_id = ?) GROUP BY model",
        (task_id,),
    ).fetchall()
    costs = [{"model": r["model"], "prompt_tokens": r["pt"],
              "completion_tokens": r["ct"], "total_cost": r["tc"]} for r in rows]
    total = sum(c["total_cost"] for c in costs)
    return {"task_id": task_id, "total_cost": total, "breakdown": costs}


@router.get("/cost/summary")
def cost_summary(user: dict = Depends(get_current_user),
                 db: sqlite3.Connection = Depends(get_db)):
    _require_admin(user)
    rows = db.execute(
        "SELECT model, SUM(prompt_tokens) as pt, SUM(completion_tokens) as ct, "
        "SUM(total_cost) as tc, COUNT(*) as games FROM cost_records GROUP BY model"
    ).fetchall()
    total_cost = sum(r["tc"] for r in rows)
    total_games = sum(r["games"] for r in rows)
    avg = total_cost / total_games if total_games > 0 else 0
    by_model = [{"model": r["model"], "prompt_tokens": r["pt"],
                 "completion_tokens": r["ct"], "total_cost": r["tc"],
                 "games": r["games"]} for r in rows]
    return {"total_cost": total_cost, "total_games": total_games,
            "avg_cost_per_game": avg, "by_model": by_model}
