"""
Game room management for LAN PvP battles.

Provides in-memory room CRUD with background garbage collection.
"""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Literal

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel

from auth import get_current_user

router = APIRouter(prefix="/api/rooms", tags=["rooms"])

# In-memory room storage
rooms: Dict[str, "GameRoom"] = {}


class GameRoom(BaseModel):
    id: str
    host_user_id: int
    host_username: str
    guest_user_id: Optional[int] = None
    guest_username: Optional[str] = None
    status: Literal["waiting", "playing", "finished"] = "waiting"
    host_deck: Optional[str] = None
    guest_deck: Optional[str] = None
    game_id: Optional[str] = None
    created_at: str = ""


class CreateRoomRequest(BaseModel):
    deck_id: str


class JoinRoomRequest(BaseModel):
    deck_id: str


@router.post("")
def create_room(
    body: CreateRoomRequest,
    user: dict = Depends(get_current_user),
) -> dict:
    room_id = str(uuid.uuid4())[:8]
    room = GameRoom(
        id=room_id,
        host_user_id=user["id"],
        host_username=user["username"],
        host_deck=body.deck_id,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    rooms[room_id] = room
    return {"room": room.model_dump()}


@router.get("")
def list_rooms(user: dict = Depends(get_current_user)) -> dict:
    """Return all waiting rooms with an is_own flag for the current user's own rooms."""
    result = []
    for room in rooms.values():
        if room.status == "waiting":
            item = room.model_dump()
            item["is_own"] = room.host_user_id == user["id"]
            result.append(item)
    return {"rooms": result}


@router.post("/{room_id}/join")
def join_room(
    room_id: str,
    body: JoinRoomRequest,
    user: dict = Depends(get_current_user),
) -> dict:
    if room_id not in rooms:
        raise HTTPException(status_code=404, detail="房间不存在")
    room = rooms[room_id]
    if room.status != "waiting":
        raise HTTPException(status_code=400, detail="房间已无法加入")
    if room.host_user_id == user["id"]:
        raise HTTPException(status_code=400, detail="不能加入自己创建的房间")
    if room.guest_user_id is not None:
        raise HTTPException(status_code=400, detail="房间已满")

    room.guest_user_id = user["id"]
    room.guest_username = user["username"]
    room.guest_deck = body.deck_id
    return {"room": room.model_dump()}


@router.post("/{room_id}/start")
def start_room(room_id: str, user: dict = Depends(get_current_user)) -> dict:
    if room_id not in rooms:
        raise HTTPException(status_code=404, detail="房间不存在")
    room = rooms[room_id]
    if room.host_user_id != user["id"]:
        raise HTTPException(status_code=403, detail="只有房主可以开始对战")
    if room.guest_user_id is None:
        raise HTTPException(status_code=400, detail="等待对手加入")
    if not room.host_deck or not room.guest_deck:
        raise HTTPException(status_code=400, detail="双方都需要选择卡组")

    room.status = "playing"
    return {"room": room.model_dump(), "message": "对战开始"}


@router.get("/{room_id}")
def get_room(room_id: str, user: dict = Depends(get_current_user)) -> dict:
    """获取单个房间信息 — 供 host/guest 轮询状态变化用"""
    if room_id not in rooms:
        raise HTTPException(status_code=404, detail="房间不存在")
    room = rooms[room_id]
    if room.host_user_id != user["id"] and room.guest_user_id != user["id"]:
        raise HTTPException(status_code=403, detail="你不在这个房间中")
    return {"room": room.model_dump()}


@router.delete("/{room_id}")
def leave_room(room_id: str, user: dict = Depends(get_current_user)) -> dict:
    if room_id not in rooms:
        raise HTTPException(status_code=404, detail="房间不存在")
    room = rooms[room_id]
    if room.host_user_id != user["id"] and room.guest_user_id != user["id"]:
        raise HTTPException(status_code=403, detail="你不在这个房间中")

    if room.host_user_id == user["id"]:
        del rooms[room_id]
    elif room.guest_user_id == user["id"]:
        room.guest_user_id = None
        room.guest_username = None
        room.guest_deck = None

    return {"success": True}


# ── Background garbage collection ─────────────────────────────────────

async def _cleanup_orphan_rooms():
    """Remove rooms that have been waiting for > 30 minutes."""
    while True:
        await asyncio.sleep(300)  # every 5 minutes
        cutoff = datetime.now(timezone.utc).isoformat()
        to_remove = []
        for rid, room in list(rooms.items()):
            if room.status == "waiting" and room.created_at:
                try:
                    created = datetime.fromisoformat(room.created_at)
                    elapsed = (datetime.now(timezone.utc) - created).total_seconds()
                    if elapsed > 1800:  # 30 min
                        to_remove.append(rid)
                except (ValueError, TypeError):
                    pass
        for rid in to_remove:
            del rooms[rid]
