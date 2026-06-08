"""Deck configuration management API for AI battle testing."""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth import get_current_user
from database import get_db

router = APIRouter(prefix="/api", tags=["decks"])

_BUILTIN_DECK_NAMES = ["archaludon_dialga_ex", "charizard_ex", "gardevori_ex", "gholdengo_ex", "klawf_terapagos", "lugia_archeops", "miraidon_ex", "origin_palkia_noctowl_vstar", "raging_bolt_ogerpon_ex", "regidrago_vstar", "terapagos_noctowl_ex"]


class DeckInfo(BaseModel):
    name: str
    path: str
    source: str
    enabled: bool = True


class DeckToggleRequest(BaseModel):
    name: str
    enabled: bool


def _ensure_deck_configs_table(db: sqlite3.Connection) -> None:
    db.execute("""CREATE TABLE IF NOT EXISTS deck_configs (
        deck_name TEXT PRIMARY KEY, enabled INTEGER DEFAULT 1)""")
    db.commit()


@router.get("/decks/config")
def list_decks(db: sqlite3.Connection = Depends(get_db)):
    """返回所有内置卡组配置列表。"""
    _ensure_deck_configs_table(db)
    rows = db.execute("SELECT deck_name, enabled FROM deck_configs").fetchall()
    config = {row[0]: bool(row[1]) for row in rows}
    decks = []
    for name in _BUILTIN_DECK_NAMES:
        decks.append({
            "name": name, "path": f"{name}.txt", "source": "builtin",
            "enabled": config.get(name, True),
        })
    return decks


@router.put("/admin/decks")
def toggle_decks(
    body: DeckToggleRequest,
    user: dict = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
):
    """Enable or disable a deck (admin only)."""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    _ensure_deck_configs_table(db)
    db.execute(
        "INSERT INTO deck_configs (deck_name, enabled) VALUES (?, ?) ON CONFLICT(deck_name) DO UPDATE SET enabled = ?",
        (body.name, int(body.enabled), int(body.enabled)),
    )
    db.commit()
    return {"name": body.name, "enabled": body.enabled}
