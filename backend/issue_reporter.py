"""Issue query and classification API for AI battle testing results."""

import json, sqlite3
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from auth import get_current_user
from database import get_db

router = APIRouter(prefix="/api/test", tags=["issues"])


class IssueMarkRequest(BaseModel):
    status: str
    duplicate_of: int | None = None


def _require_admin(user: dict) -> None:
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")


@router.get("/issues")
def list_issues(task_id: int | None = Query(None), status: str | None = Query(None),
                category: str | None = Query(None), user: dict = Depends(get_current_user),
                db: sqlite3.Connection = Depends(get_db)):
    _require_admin(user)
    q, p = "SELECT * FROM detected_issues WHERE 1=1", []
    if task_id is not None: q += " AND task_id = ?"; p.append(task_id)
    if status: q += " AND status = ?"; p.append(status)
    if category: q += " AND category = ?"; p.append(category)
    rows = db.execute(q + " ORDER BY created_at DESC", p).fetchall()
    return {"issues": [dict(r) for r in rows]}


@router.get("/issues/summary")
def issue_summary(task_id: int | None = Query(None), user: dict = Depends(get_current_user),
                  db: sqlite3.Connection = Depends(get_db)):
    _require_admin(user)
    q = "SELECT fingerprint_hash, error_signature, category, severity, COUNT(*) as cnt, status FROM detected_issues"
    p = []
    if task_id is not None: q += " WHERE task_id = ?"; p.append(task_id)
    q += " GROUP BY fingerprint_hash ORDER BY cnt DESC"
    return {"summary": [dict(r) for r in db.execute(q, p).fetchall()]}


@router.get("/issues/{issue_id}")
def get_issue(issue_id: int, user: dict = Depends(get_current_user),
              db: sqlite3.Connection = Depends(get_db)):
    _require_admin(user)
    r = db.execute("SELECT * FROM detected_issues WHERE id = ?", (issue_id,)).fetchone()
    if not r: raise HTTPException(status_code=404, detail="Issue not found")
    result = dict(r)
    result["state_snapshot"] = json.loads(r["state_snapshot"]) if r["state_snapshot"] else None
    result["last_n_actions"] = json.loads(r["last_n_actions"]) if r["last_n_actions"] else None
    return result


@router.patch("/issues/{issue_id}")
def mark_issue(issue_id: int, body: IssueMarkRequest,
               user: dict = Depends(get_current_user),
               db: sqlite3.Connection = Depends(get_db)):
    _require_admin(user)
    if not db.execute("SELECT id FROM detected_issues WHERE id = ?", (issue_id,)).fetchone():
        raise HTTPException(status_code=404, detail="Issue not found")
    if body.status not in ("confirmed", "false_positive", "duplicate"):
        raise HTTPException(status_code=400, detail="Invalid status")
    db.execute("UPDATE detected_issues SET status=?, marked_by=?, marked_at=? WHERE id=?",
               (body.status, user["id"], datetime.now(timezone.utc).isoformat(), issue_id))
    db.commit()
    return {"id": issue_id, "status": body.status}
