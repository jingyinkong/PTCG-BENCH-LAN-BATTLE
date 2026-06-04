"""
Authentication API routes for PTCG-Bench.
"""

import re
import secrets
from typing import Optional
import sqlite3

import bcrypt
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, field_validator

from database import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not (3 <= len(v) <= 20):
            raise ValueError("用户名长度须为 3-20 个字符")
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("用户名只能包含字母、数字和下划线")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("密码长度须至少 6 个字符")
        return v


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    success: bool = True
    token: Optional[str] = None
    username: Optional[str] = None
    id: Optional[int] = None


class UserInfo(BaseModel):
    id: int
    username: str
    created_at: str


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def _generate_token() -> str:
    return secrets.token_urlsafe(32)


def _cleanup_expired_sessions(db: sqlite3.Connection) -> None:
    db.execute("DELETE FROM sessions WHERE created_at < datetime('now', '-1 day')")
    db.commit()


def get_current_user(
    authorization: Optional[str] = Header(None),
) -> dict:
    if not authorization:
        raise HTTPException(status_code=401, detail="未提供认证 token")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="认证格式错误")

    token = authorization[len("Bearer "):]
    import sqlite3 as _sqlite3
    from database import DB_PATH
    db = _sqlite3.connect(str(DB_PATH))
    db.row_factory = _sqlite3.Row
    try:
        row = db.execute(
            "SELECT u.id, u.username, u.created_at FROM users u "
            "JOIN sessions s ON s.user_id = u.id "
            "WHERE s.token = ?",
            (token,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=401, detail="token 无效或已过期")
        return {"id": row["id"], "username": row["username"], "created_at": row["created_at"]}
    finally:
        db.close()


@router.post("/register")
def register(body: RegisterRequest, db: sqlite3.Connection = Depends(get_db)) -> AuthResponse:
    existing = db.execute("SELECT id FROM users WHERE username = ?", (body.username,)).fetchone()
    if existing:
        raise HTTPException(status_code=409, detail="用户名已存在")
    hashed = _hash_password(body.password)
    db.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (body.username, hashed))
    db.commit()
    return AuthResponse(success=True, username=body.username)


@router.post("/login")
def login(body: LoginRequest, db: sqlite3.Connection = Depends(get_db)) -> AuthResponse:
    _cleanup_expired_sessions(db)
    row = db.execute(
        "SELECT id, password_hash FROM users WHERE username = ?", (body.username,)
    ).fetchone()
    if row is None or not _verify_password(body.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = _generate_token()
    db.execute("INSERT INTO sessions (user_id, token) VALUES (?, ?)", (row["id"], token))
    db.commit()
    return AuthResponse(success=True, token=token, username=body.username, id=row["id"])


@router.post("/logout")
def logout(
    authorization: Optional[str] = Header(None),
    db: sqlite3.Connection = Depends(get_db),
) -> AuthResponse:
    if authorization and authorization.startswith("Bearer "):
        token = authorization[len("Bearer "):]
        db.execute("DELETE FROM sessions WHERE token = ?", (token,))
        db.commit()
    return AuthResponse(success=True)


@router.get("/me")
def me(user: dict = Depends(get_current_user)) -> UserInfo:
    return UserInfo(id=user["id"], username=user["username"], created_at=user["created_at"])
