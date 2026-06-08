"""Admin settings API — API key management for LLM backends."""

import os, sqlite3
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from auth import get_current_user
from database import get_db

router = APIRouter(prefix="/api/admin", tags=["settings"])

PROVIDER_ENV_MAP = {
    "deepseek": "DEEPSEEK_API_KEY", "openrouter": "OPENROUTER_API_KEY",
    "zai": "ZAI_API_KEY", "dashscope": "DASHSCOPE_API_KEY", "minimax": "MINIMAX_API_KEY",
}


class ApiKeyUpdate(BaseModel):
    provider: str
    api_key: str


class ApiKeyStatus(BaseModel):
    provider: str
    configured: bool
    masked_key: str


def _ensure_settings_table(db: sqlite3.Connection) -> None:
    db.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    db.commit()


def get_api_key(provider: str) -> str:
    """Get API key: env first, database fallback."""
    env_key = PROVIDER_ENV_MAP.get(provider, f"{provider.upper()}_API_KEY")
    value = os.getenv(env_key, "")
    if value:
        return value
    try:
        from database import DB_PATH
        db = sqlite3.connect(str(DB_PATH))
        row = db.execute("SELECT value FROM settings WHERE key=?", (env_key,)).fetchone()
        db.close()
        return row[0] if row else ""
    except Exception:
        return ""


@router.get("/settings/api-keys")
def list_api_keys(user: dict = Depends(get_current_user)):
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    result = []
    for p in PROVIDER_ENV_MAP:
        key = get_api_key(p)
        masked = key[:4] + "****" + key[-4:] if len(key) > 8 else ("****" if key else "")
        result.append(ApiKeyStatus(provider=p, configured=bool(key), masked_key=masked))
    return {"providers": [r.model_dump() for r in result]}


@router.put("/settings/api-keys")
def update_api_key(body: ApiKeyUpdate, user: dict = Depends(get_current_user),
                   db: sqlite3.Connection = Depends(get_db)):
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    env_key = PROVIDER_ENV_MAP.get(body.provider, f"{body.provider.upper()}_API_KEY")
    _ensure_settings_table(db)
    db.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=?",
               (env_key, body.api_key, body.api_key))
    db.commit()
    os.environ[env_key] = body.api_key
    return {"provider": body.provider, "configured": True}
