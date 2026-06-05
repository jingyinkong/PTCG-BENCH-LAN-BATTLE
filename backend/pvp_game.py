"""
PvP WebSocket battle handler.

Manages two-player WebSocket rooms, game engine lifecycle,
message broadcasting, turn control, and disconnect/reconnect logic.
"""

import asyncio

from i18n.translator import t
import json
import secrets
import time
from typing import Dict, Optional

from fastapi import WebSocket, WebSocketDisconnect

from database import DB_PATH
from game_rooms import rooms as game_rooms

import sqlite3

# Active PvP WebSocket connections: room_id -> {player1|player2: WebSocket}
active_connections: Dict[str, Dict[str, WebSocket]] = {}
# Reconnection timers: room_id -> {player1|player2: asyncio.Task}
reconnect_timers: Dict[str, Dict[str, asyncio.Task]] = {}


def _get_user_from_token(token: str) -> Optional[dict]:
    """Validate a session token and return user info, or None."""
    db = sqlite3.connect(str(DB_PATH))
    db.row_factory = sqlite3.Row
    try:
        row = db.execute(
            "SELECT u.id, u.username FROM users u "
            "JOIN sessions s ON s.user_id = u.id "
            "WHERE s.token = ?", (token,)
        ).fetchone()
        if row:
            return {"id": row["id"], "username": row["username"]}
        return None
    finally:
        db.close()


async def _broadcast_state(room_id: str, msg: dict) -> None:
    """Send a message to both players in a room."""
    conns = active_connections.get(room_id, {})
    for ws in conns.values():
        try:
            await ws.send_json(msg)
        except Exception:
            pass


async def _handle_reconnect_timeout(room_id: str, player: str) -> None:
    """Called when the 30-second reconnection window expires."""
    await asyncio.sleep(30)
    # Check if player reconnected during the window
    conns = active_connections.get(room_id, {})
    if player in conns and conns[player].client_state.name == "CONNECTED":
        return  # reconnected
    # Opponent wins by forfeit
    room = game_rooms.get(room_id)
    if room:
        opponent = "player1" if player == "player2" else "player2"
        await _broadcast_state(room_id, {
            "type": "OPPONENT_DISCONNECTED",
            "message": t("opponent_timeout")
        })
        # Record match
        await _record_match_result(room_id, winner=opponent, forfeit=True)
        # Cleanup
        _cleanup_room(room_id)


def _cleanup_room(room_id: str) -> None:
    """Remove room and game state."""
    active_connections.pop(room_id, None)
    reconnect_timers.pop(room_id, None)
    room = game_rooms.get(room_id)
    if room:
        room.status = "finished"
    # Don't delete room entry so match record can reference it


async def _record_match_result(
    room_id: str, winner: str = "player1", forfeit: bool = False
) -> None:
    """Record match result in the database."""
    from ptcg.core.envs import PokemonTCG
    room = game_rooms.get(room_id)
    if not room:
        return

    db = sqlite3.connect(str(DB_PATH))
    try:
        winner_uid = room.host_user_id if winner == "player1" else room.guest_user_id
        loser_uid = room.guest_user_id if winner == "player1" else room.host_user_id

        db.execute(
            """INSERT INTO match_records
            (game_room_id, player1_user_id, player2_user_id,
             winner_user_id, loser_user_id,
             deck1_name, deck2_name, total_turns, duration_seconds)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                room_id, room.host_user_id, room.guest_user_id,
                winner_uid, loser_uid,
                room.host_deck, room.guest_deck,
                0, 0.0
            )
        )
        db.commit()
    finally:
        db.close()


class PvPGameManager:
    """Manages the lifecycle of a PvP WebSocket game."""

    def __init__(self, room_id: str):
        self.room_id = room_id

    async def handle_connection(self, websocket: WebSocket, token: str) -> str:
        """Accept WebSocket, authenticate, assign player role. Returns 'player1' or 'player2'."""
        user = _get_user_from_token(token)
        if not user:
            await websocket.close(code=4001, reason="Invalid token")
            return ""

        room = game_rooms.get(self.room_id)
        if not room:
            await websocket.close(code=4004, reason="Room not found")
            return ""

        # Assign player role
        if user["id"] == room.host_user_id:
            player = "player1"
        elif user["id"] == room.guest_user_id:
            player = "player2"
        else:
            await websocket.close(code=4003, reason="Not in this room")
            return ""

        # Track connection
        if self.room_id not in active_connections:
            active_connections[self.room_id] = {}
        active_connections[self.room_id][player] = websocket

        # Cancel reconnection timer if exists
        timers = reconnect_timers.get(self.room_id, {})
        if player in timers:
            timers[player].cancel()

        return player

    async def handle_disconnect(self, player: str) -> None:
        """Notify the other player immediately, then start reconnection timer."""
        # Immediately tell the opponent that this player left
        conns = active_connections.get(self.room_id, {})
        opponent = "player1" if player == "player2" else "player2"
        opponent_ws = conns.get(opponent)
        if opponent_ws is not None:
            try:
                await opponent_ws.send_json({
                    "type": "OPPONENT_LEFT",
                    "message": t("opponent_disconnected"),
                })
            except Exception:
                pass

        # Still start the 30-second reconnection timer for potential reconnect
        if self.room_id not in reconnect_timers:
            reconnect_timers[self.room_id] = {}
        reconnect_timers[self.room_id][player] = asyncio.create_task(
            _handle_reconnect_timeout(self.room_id, player)
        )

    def is_both_connected(self) -> bool:
        conns = active_connections.get(self.room_id, {})
        return "player1" in conns and "player2" in conns

    def validate_turn(self, player: str, turn: str) -> bool:
        """Validate that the player is allowed to act on this turn."""
        # turn is in format "PLAYER1" or "PLAYER2"
        expected = "PLAYER1" if player == "player1" else "PLAYER2"
        return turn == expected

    def validate_message(self, data: dict) -> Optional[str]:
        """Validate WebSocket message structure. Returns error string or None."""
        if not isinstance(data, dict):
            return t("message_bad_format")
        if data.get("type") != "ACTION":
            return None  # Non-action messages don't need validation
        if "action_index" not in data:
            return t("message_missing_action_index")
        if not isinstance(data["action_index"], int):
            return t("message_action_index_int")
        return None
