"""
Authentication API routes for PTCG-Bench.
"""

import re
import secrets
from typing import Optional
import sqlite3

import bcrypt
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, field_validator

from database import get_db
from i18n.translator import t, parse_accept_language

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not (3 <= len(v) <= 20):
            raise ValueError(t("username_length"))
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError(t("username_chars"))
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError(t("password_length"))
        return v


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    success: bool = True
    token: Optional[str] = None
    username: Optional[str] = None
    id: Optional[int] = None
    is_admin: bool = False


class UserInfo(BaseModel):
    id: int
    username: str
    is_admin: bool = False
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
        raise HTTPException(status_code=401, detail=t("auth_no_token"))
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail=t("auth_bad_format"))

    token = authorization[len("Bearer "):]
    import sqlite3 as _sqlite3
    from database import DB_PATH
    db = _sqlite3.connect(str(DB_PATH))
    db.row_factory = _sqlite3.Row
    try:
        row = db.execute(
            "SELECT u.id, u.username, u.is_admin, u.created_at FROM users u "
            "JOIN sessions s ON s.user_id = u.id "
            "WHERE s.token = ?",
            (token,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=401, detail=t("auth_invalid_token"))
        return {"id": row["id"], "username": row["username"], "is_admin": bool(row["is_admin"]), "created_at": row["created_at"]}
    finally:
        db.close()


@router.post("/register")
def register(body: RegisterRequest, db: sqlite3.Connection = Depends(get_db)) -> AuthResponse:
    existing = db.execute("SELECT id FROM users WHERE username = ?", (body.username,)).fetchone()
    if existing:
        raise HTTPException(status_code=409, detail=t("auth_username_taken"))
    hashed = _hash_password(body.password)
    db.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (body.username, hashed))
    db.commit()
    return AuthResponse(success=True, username=body.username)


@router.post("/login")
def login(body: LoginRequest, db: sqlite3.Connection = Depends(get_db)) -> AuthResponse:
    _cleanup_expired_sessions(db)
    row = db.execute(
        "SELECT id, password_hash, is_admin FROM users WHERE username = ?", (body.username,)
    ).fetchone()
    if row is None or not _verify_password(body.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail=t("auth_wrong_credentials"))
    token = _generate_token()
    db.execute("INSERT INTO sessions (user_id, token) VALUES (?, ?)", (row["id"], token))
    db.commit()
    return AuthResponse(success=True, token=token, username=body.username, id=row["id"], is_admin=bool(row["is_admin"]))


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
    return UserInfo(id=user["id"], username=user["username"], is_admin=user.get("is_admin", False), created_at=user["created_at"])
