"""
PTCG Backend API Server
Provides REST and WebSocket endpoints for the game engine
"""

import os
import sys
from pathlib import Path

# Add repository root to path for local development imports.
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import json
import re
import secrets
import uuid
from importlib.resources import files
from typing import Any, Dict, List, Optional

from card_image_service import card_image_service
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from auth import router as auth_router
from game_rooms import router as rooms_router, rooms as game_rooms
from match_records import router as match_records_router
from pvp_game import PvPGameManager, active_connections, _get_user_from_token, _broadcast_state, _record_match_result, _cleanup_room
from engine_patches import apply_patches
from i18n.translator import t

# Apply engine patches for bench selection during initial setup
apply_patches()

from ptcgbench.agents.charizard_heuristic_agent import CharizardHeuristicAgent
from ptcgbench.agents.common.profile import AgentProfile
from ptcgbench.agents.random_agent import RandomAgent
from ptcgbench.agents.react_agent import ReActAgent
from ptcg.core.action import Action
from ptcg.core.envs import PokemonTCG

app = FastAPI(title="PTCG API", version="1.0.0")

# CORS configuration
BATTLE_LOG_DIR = Path(__file__).parent / "battle_log"

_default_origins = "http://localhost:3000,http://localhost:5173,http://localhost:5174,http://localhost:5175,http://localhost:5176"
_lan_mode = os.environ.get("LAN_MODE", "").lower() in ("1", "true", "yes")
if _lan_mode:
    ALLOWED_ORIGINS = ["*"]
else:
    ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", _default_origins).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register auth routes and game rooms
app.include_router(auth_router)
app.include_router(rooms_router)
app.include_router(match_records_router)

# Game storage
games: Dict[str, Dict] = {}


# ============================================================================
# Models
# ============================================================================


class GameConfig(BaseModel):
    deck1: Optional[str] = None
    deck2: Optional[str] = None
    seed: int = 422
    agent: Optional[str] = None  # "random" | "charizard_heuristic" | "skillevolving" | None
    agent_player: str = "player2"  # which player the agent controls
    agent_model: Optional[str] = None  # model string for LLM agent


class ActionRequest(BaseModel):
    action_index: int  # Index in available_actions list


# ============================================================================
# Helper Functions
# ============================================================================


def serialize_state(state) -> Dict[str, Any]:
    """Serialize game state for JSON response"""
    return state.to_dict()


def serialize_action(action: Action) -> Dict[str, Any]:
    """Serialize action for JSON response"""
    return action.to_dict()


def serialize_available_actions(actions: List[Action]) -> List[Dict[str, Any]]:
    """Serialize list of available actions"""
    return [serialize_action(action) for action in actions]


def serialize_prompt(prompt) -> Optional[Dict[str, Any]]:
    """Serialize ChooseCardPrompt for JSON response"""
    if prompt is None:
        return None
    if prompt.hidden:
        candidates = [f"Hidden Card #{i + 1}" for i in range(len(prompt.candidates))]
    else:
        candidates = [card.name for card in prompt.candidates]
    result = {
        "minCnt": prompt.min_cnt,
        "maxCnt": prompt.max_cnt,
        "candidates": candidates,
        "hidden": prompt.hidden,
        "tips": prompt.tips,
    }
    if prompt.source and hasattr(prompt.source, "name"):
        result["source"] = prompt.source.name
    return result


# ============================================================================
# REST API Endpoints
# ============================================================================


def _finalize_game_if_done(game: Dict) -> None:
    """Save replay into agent's battle record when a game finishes."""
    env = game["env"]
    agent = game.get("agent")
    if env.recorder is None or agent is None:
        return
    br = getattr(agent, "_battle_record", None)
    if br is not None:
        br.save_replay(env.recorder.file_path)


@app.get("/api/lan/server-info")
async def server_info():
    """Return LAN server info for client discovery."""
    import socket
    hostname = socket.gethostname()
    try:
        lan_ip = socket.gethostbyname(hostname)
    except socket.gaierror:
        lan_ip = "127.0.0.1"
    return {"host": lan_ip, "port": 8000, "name": hostname}


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "PTCG API is running"}


@app.get("/api/replays")
async def list_replays():
    """List available replay JSONL files"""
    files = sorted(BATTLE_LOG_DIR.glob("*.jsonl"), key=lambda f: f.stat().st_mtime, reverse=True)
    return [
        {"filename": f.name, "size": f.stat().st_size, "mtime": f.stat().st_mtime} for f in files
    ]


@app.get("/api/replays/{filename}")
async def get_replay(filename: str):
    """Return all events from a JSONL replay file"""
    filepath = BATTLE_LOG_DIR / filename
    if not filepath.exists() or filepath.suffix != ".jsonl":
        return {"error": "Replay not found"}
    events = []
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return {"filename": filename, "events": events}


@app.get("/api/agents")
async def list_agents():
    """List available agent types"""
    has_openrouter = bool(os.environ.get("OPENROUTER_API_KEY"))
    has_deepseek = bool(os.environ.get("DEEPSEEK_API_KEY"))
    llm_available = has_openrouter or has_deepseek

    react_models = []
    if has_openrouter:
        react_models += [
            {"id": "openai/gpt-5.4", "name": "GPT-5.4", "provider": "OpenAI"},
            {"id": "openai/gpt-5.4-nano", "name": "GPT-5.4 Nano", "provider": "OpenAI"},
            {
                "id": "anthropic/claude-sonnet-4.6",
                "name": "Claude Sonnet 4.6",
                "provider": "Anthropic",
            },
            {
                "id": "anthropic/claude-haiku-4.5",
                "name": "Claude Haiku 4.5",
                "provider": "Anthropic",
            },
            {"id": "google/gemini-3.1-pro-preview", "name": "Gemini 3.1 Pro", "provider": "Google"},
            {"id": "google/gemini-3-flash-preview", "name": "Gemini 3 Flash", "provider": "Google"},
            {"id": "qwen/qwen3.6-plus", "name": "Qwen 3.6 Plus", "provider": "Qwen"},
            {"id": "qwen/qwen3.5-flash-02-23", "name": "Qwen 3.5 Flash", "provider": "Qwen"},
        ]
    if has_deepseek:
        react_models += [
            {"id": "deepseek-v4-pro", "name": "DeepSeek V4 Pro", "provider": "DeepSeek"},
            {"id": "deepseek-v4-flash", "name": "DeepSeek V4 Flash", "provider": "DeepSeek"},
        ]

    agents = [
        {
            "id": "random",
            "name": "Random Agent",
            "description": "Selects actions uniformly at random. Fast and unpredictable.",
            "requiresModel": False,
            "available": True,
        },
        {
            "id": "charizard_heuristic",
            "name": "Charizard Heuristic Agent",
            "description": "Fixed rule-based policy tuned for the bundled Charizard ex deck.",
            "requiresModel": False,
            "available": True,
        },
        {
            "id": "react",
            "name": "ReAct Agent",
            "description": "Reasoning + Acting loop: thinks step-by-step then calls game actions.",
            "requiresModel": True,
            "available": llm_available,
            "unavailableReason": None
            if llm_available
            else "No API key set (OPENROUTER_API_KEY or DEEPSEEK_API_KEY)",
            "models": react_models,
            "defaultModel": react_models[0]["id"] if react_models else "",
        },
        {
            "id": "skillevolving",
            "name": "Skill Evolving Agent",
            "description": "ReAct + reflection and skill memory for long-term improvement.",
            "requiresModel": True,
            "available": llm_available,
            "unavailableReason": None
            if llm_available
            else "No API key set (OPENROUTER_API_KEY or DEEPSEEK_API_KEY)",
            "models": react_models,
            "defaultModel": react_models[0]["id"] if react_models else "",
        },
    ]
    return agents


@app.get("/api/decks")
async def list_decks():
    """List available decks with parsed card info"""
    try:
        deck_files = sorted(
            deck_file
            for deck_file in files("ptcg.decks").iterdir()
            if deck_file.name.endswith(".txt")
        )
    except ModuleNotFoundError:
        return []

    energy_type_re = re.compile(r"\{([A-Za-z]+)\}")
    decks = []

    for deck_file in deck_files:
        deck_name = deck_file.stem
        display_name = deck_name.replace("_", " ").title()

        pokemon_list: List[Dict] = []
        trainer_count = 0
        energy_count = 0
        energy_types: set = set()
        current_section: Optional[str] = None

        try:
            with deck_file.open(encoding="utf-8") as f:
                for raw in f:
                    line = raw.strip()
                    if not line:
                        continue
                    if "Pokémon:" in line or "Pokemon:" in line:
                        current_section = "pokemon"
                    elif line.startswith("Trainer:"):
                        current_section = "trainer"
                        try:
                            trainer_count = int(line.split(":")[1].strip())
                        except (IndexError, ValueError):
                            pass
                    elif line.startswith("Energy:"):
                        current_section = "energy"
                        try:
                            energy_count = int(line.split(":")[1].strip())
                        except (IndexError, ValueError):
                            pass
                    elif current_section and line[0].isdigit():
                        parts = line.split()
                        if len(parts) >= 4:
                            count = int(parts[0])
                            name = " ".join(parts[1:-2])
                            if current_section == "pokemon":
                                pokemon_list.append({"count": count, "name": name})
                            elif current_section == "energy":
                                for m in energy_type_re.findall(name):
                                    energy_types.add(m.upper())
        except Exception as exc:
            print(f"Error parsing deck {deck_file}: {exc}")
            continue

        pokemon_count = sum(p["count"] for p in pokemon_list)
        decks.append(
            {
                "id": deck_name,
                "displayName": display_name,
                "pokemonCount": pokemon_count,
                "trainerCount": trainer_count,
                "energyCount": energy_count,
                "keyPokemon": [p["name"] for p in pokemon_list[:6]],
                "energyTypes": sorted(energy_types),
            }
        )

    return decks


@app.get("/api/leaderboard")
async def get_leaderboard():
    """Return agent ratings from bench_data/ratings.json"""
    ratings_file = Path(__file__).parent.parent / "bench_data" / "ratings.json"
    if not ratings_file.exists():
        return {"agents": []}
    data = json.loads(ratings_file.read_text())
    agents = []
    for agent_id, fields in data.items():
        agents.append({"agent_id": agent_id, **fields})
    agents.sort(key=lambda a: a["mu"], reverse=True)
    return {"agents": agents}


@app.get("/api/cards/images")
async def get_all_card_images():
    """Get all card image URLs"""
    return card_image_service.get_all_card_images()


@app.get("/api/card/{card_name}/image")
async def get_card_image(card_name: str):
    """Get image URL for a specific card"""
    image_url = card_image_service.get_card_image_url(card_name)
    if image_url:
        return {"name": card_name, "url": image_url}
    return {"error": "Card not found"}


@app.post("/api/game/create")
async def create_game(config: GameConfig):
    """Create a new game instance"""
    game_id = str(uuid.uuid4())

    # Create environment
    env = PokemonTCG(seed=config.seed, verbose=False, deck1=config.deck1, deck2=config.deck2)

    # Initialize game
    obs, reward, done, info = env.reset()

    # Setup agent if configured
    agent_instance = None
    if config.agent == "random":
        agent_instance = RandomAgent()
    elif config.agent == "charizard_heuristic":
        agent_instance = CharizardHeuristicAgent(seed=config.seed)
    elif config.agent == "react":
        model = config.agent_model or "deepseek-v4-flash"
        agent_instance = ReActAgent(model=model)
    elif config.agent == "skillevolving":
        from ptcgbench.agents.skill_evolving_agent import SkillEvolvingAgent

        model = config.agent_model or "deepseek-v4-flash"
        agent_instance = SkillEvolvingAgent(model=model)

    # Notify agent of game start with deck info
    if agent_instance is not None and hasattr(agent_instance, "notify_game_start"):
        deck1_name = AgentProfile.deck_name_from_path(config.deck1) if config.deck1 else "default"
        deck2_name = AgentProfile.deck_name_from_path(config.deck2) if config.deck2 else "default"
        if config.agent_player == "player1":
            agent_instance.notify_game_start(deck1_name, deck2_name, opponent_name="human")
        else:
            agent_instance.notify_game_start(deck2_name, deck1_name, opponent_name="human")

    # Store game
    games[game_id] = {
        "env": env,
        "state": obs,
        "info": info,
        "config": config.model_dump(),
        "agent": agent_instance,
        "agent_player": config.agent_player,
    }

    return {
        "gameId": game_id,
        "state": serialize_state(obs),
        "availableActions": serialize_available_actions(info["raw_available_actions"]),
        "turn": info["turn"].name,
        "done": done,
        "isChoosingCard": info.get("is_choosing_card", False),
        "chooseCardPrompt": serialize_prompt(info.get("prompt")),
        "vsAgent": config.agent is not None,
        "agentPlayer": config.agent_player if config.agent else None,
        "agentType": config.agent,
        "agentModel": config.agent_model,
    }


@app.get("/api/game/{game_id}/state")
async def get_game_state(game_id: str):
    """Get current game state"""
    if game_id not in games:
        return {"error": "Game not found"}

    game = games[game_id]
    env = game["env"]

    return {
        "state": serialize_state(env.gamestate),
        "availableActions": serialize_available_actions(game["info"]["raw_available_actions"]),
        "turn": game["info"]["turn"].name,
        "timestep": env.gamestate.timestep,
        "done": False,
    }


@app.post("/api/game/{game_id}/action")
async def execute_action(game_id: str, request: ActionRequest):
    """Execute an action in the game"""
    if game_id not in games:
        return {"error": "Game not found"}

    game = games[game_id]
    env = game["env"]
    available_actions = game["info"]["raw_available_actions"]

    # Validate action index
    if request.action_index < 0 or request.action_index >= len(available_actions):
        return {"error": "Invalid action index"}

    # Execute action
    action = available_actions[request.action_index]
    obs, reward, done, info = env.step(action)

    # Update game state
    games[game_id]["state"] = obs
    games[game_id]["info"] = info

    response = {
        "success": True,
        "state": serialize_state(obs),
        "availableActions": serialize_available_actions(info["raw_available_actions"]),
        "reward": reward,
        "done": done,
        "turn": info["turn"].name if not done else None,
        "isChoosingCard": info.get("is_choosing_card", False),
        "chooseCardPrompt": serialize_prompt(info.get("prompt")),
    }

    if done:
        response["winner"] = info.get("winner").name if info.get("winner") else None
        _finalize_game_if_done(game)

    return response


@app.post("/api/game/{game_id}/agent-step")
async def agent_step(game_id: str):
    """Let the configured agent take one action"""
    if game_id not in games:
        return {"error": "Game not found"}

    game = games[game_id]
    agent = game.get("agent")
    if not agent:
        return {"error": "No agent configured for this game"}

    env = game["env"]
    obs = game["state"]
    info = game["info"]

    # Run predict in a thread — LLMAgent uses run_until_complete() which can't
    # nest inside FastAPI's already-running event loop.
    action = await asyncio.to_thread(agent.predict, obs, info)

    # Execute action
    obs, reward, done, info = env.step(action)

    games[game_id]["state"] = obs
    games[game_id]["info"] = info

    response = {
        "success": True,
        "state": serialize_state(obs),
        "availableActions": serialize_available_actions(info["raw_available_actions"]),
        "reward": reward,
        "done": done,
        "turn": info["turn"].name if not done else None,
        "isChoosingCard": info.get("is_choosing_card", False),
        "chooseCardPrompt": serialize_prompt(info.get("prompt")),
        "actionTaken": serialize_action(action),
    }

    if done:
        response["winner"] = info.get("winner").name if info.get("winner") else None
        _finalize_game_if_done(game)

    return response


@app.delete("/api/game/{game_id}")
async def delete_game(game_id: str):
    """Delete a game instance"""
    if game_id in games:
        del games[game_id]
        return {"success": True}
    return {"error": "Game not found"}


# ============================================================================
# WebSocket Endpoint
# ============================================================================


@app.websocket("/ws/game/{game_id}")
async def websocket_game(websocket: WebSocket, game_id: str):
    """WebSocket endpoint for real-time game updates"""
    await websocket.accept()

    try:
        # Check if game exists, if not create it
        if game_id not in games:
            await websocket.send_json({"type": "ERROR", "message": "Game not found"})
            await websocket.close()
            return

        game = games[game_id]
        env = game["env"]

        # Send initial state
        await websocket.send_json(
            {
                "type": "STATE_UPDATE",
                "state": serialize_state(env.gamestate),
                "availableActions": serialize_available_actions(
                    game["info"]["raw_available_actions"]
                ),
                "turn": game["info"]["turn"].name,
                "timestep": env.gamestate.timestep,
            }
        )

        while True:
            # Receive action from client
            data = await websocket.receive_text()
            message = json.loads(data)

            if message["type"] == "ACTION":
                action_index = message["action_index"]
                available_actions = game["info"]["raw_available_actions"]

                if 0 <= action_index < len(available_actions):
                    action = available_actions[action_index]
                    obs, reward, done, info = env.step(action)

                    # Update game state
                    games[game_id]["state"] = obs
                    games[game_id]["info"] = info

                    # Send state update
                    await websocket.send_json(
                        {
                            "type": "STATE_UPDATE",
                            "state": serialize_state(obs),
                            "availableActions": serialize_available_actions(
                                info["raw_available_actions"]
                            ),
                            "reward": reward,
                            "done": done,
                            "turn": info["turn"].name if not done else None,
                        }
                    )

                    if done:
                        await websocket.send_json(
                            {
                                "type": "GAME_OVER",
                                "winner": info.get("winner").name if info.get("winner") else None,
                            }
                        )
                        break
                else:
                    await websocket.send_json({"type": "ERROR", "message": "Invalid action index"})

            elif message["type"] == "GET_STATE":
                await websocket.send_json(
                    {
                        "type": "STATE_UPDATE",
                        "state": serialize_state(env.gamestate),
                        "availableActions": serialize_available_actions(
                            game["info"]["raw_available_actions"]
                        ),
                        "turn": game["info"]["turn"].name,
                        "timestep": env.gamestate.timestep,
                    }
                )

    except WebSocketDisconnect:
        print(f"WebSocket disconnected for game {game_id}")
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.send_json({"type": "ERROR", "message": str(e)})


# ============================================================================
# PvP WebSocket Endpoint
# ============================================================================

# Per-room coin toss state for interactive PTCG coin toss protocol
coin_toss_states: Dict[str, dict] = {}

def _filter_state_for_player(state_dict: dict, viewer: str) -> dict:
    """Replace the opponent's hand cards with hidden placeholders.

    In PTCG, each player should only see:
    - Their own hand (face up)
    - Both players' bench, active, discard (public knowledge)
    - Prize cards and deck are always hidden regardless
    """
    opponent = "player2" if viewer == "player1" else "player1"
    # Shallow-copy top level, deep-copy the opponent section to avoid mutating original
    result = {k: v for k, v in state_dict.items()}
    if opponent in result and isinstance(result[opponent], dict):
        opp = {k: v for k, v in result[opponent].items()}
        hand_size = len(opp.get("hand", []))
        opp["hand"] = [
            {"name": "???", "set_name": "", "number": "hidden", "hidden": True}
            for _ in range(hand_size)
        ]
        result[opponent] = opp
    return result


async def _send_state_to_players(room_id: str, base_msg: dict) -> None:
    """Send per-player filtered state to each connected WebSocket.

    Filters:
    - Hand cards: opponent's hand is hidden
    - chooseCardPrompt: only sent to the player whose turn it is
    """
    conns = active_connections.get(room_id, {})
    turn = base_msg.get("turn", "")
    for role, ws in conns.items():
        try:
            msg = {k: v for k, v in base_msg.items()}
            if "state" in msg:
                msg["state"] = _filter_state_for_player(msg["state"], role)
            # Only the player whose turn it is should see the card selection prompt
            is_my_turn = (role == "player1" and turn == "PLAYER1") or (
                role == "player2" and turn == "PLAYER2"
            )
            if not is_my_turn:
                msg["isChoosingCard"] = False
                msg["chooseCardPrompt"] = None
            await ws.send_json(msg)
        except Exception:
            pass


@app.websocket("/ws/room/{room_id}")
async def websocket_pvp_room(websocket: WebSocket, room_id: str):
    """WebSocket endpoint for two-player PvP battles with coin-toss and hidden hands."""
    token = websocket.query_params.get("token", "")
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return

    manager = PvPGameManager(room_id)

    await websocket.accept()
    player = await manager.handle_connection(websocket, token)
    if not player:
        return

    # Create game engine instance once both players are connected
    if manager.is_both_connected() and room_id not in coin_toss_states:
        room = game_rooms.get(room_id)
        if room and room.status == "playing" and room.host_deck and room.guest_deck:
            # ── PTCG Coin Toss (interactive protocol) ──
            # Step 1: Randomly pick who calls heads/tails
            caller = "player1" if secrets.randbelow(2) == 1 else "player2"
            caller_name = room.host_username if caller == "player1" else room.guest_username
            coin_toss_states[room_id] = {
                "phase": "call",
                "caller": caller,
                "caller_name": caller_name,
                "caller_choice": None,
                "coin": None,
                "chooser": None,
                "turn_choice": None,
            }
            # Notify both: "X will call heads or tails"
            for ws in active_connections.get(room_id, {}).values():
                try:
                    await ws.send_json({
                        "type": "COIN_TOSS",
                        "phase": "call",
                        "caller": caller,
                        "caller_name": caller_name,
                    })
                except Exception:
                    pass

    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "ERROR", "message": t("game_invalid_json")})
                continue

            # ── Coin Toss Protocol Messages ──
            ct = coin_toss_states.get(room_id)
            if ct and message.get("type") == "COIN_TOSS_CALL":
                if player != ct["caller"]:
                    await websocket.send_json({"type": "ERROR", "message": t("coin_not_your_call")})
                    continue
                choice = message.get("choice", "")
                if choice not in ("heads", "tails"):
                    await websocket.send_json({"type": "ERROR", "message": t("coin_invalid_choice")})
                    continue
                ct["caller_choice"] = choice
                ct["coin"] = "heads" if secrets.randbelow(2) == 1 else "tails"
                ct["chooser"] = ct["caller"] if choice == ct["coin"] else (
                    "player2" if ct["caller"] == "player1" else "player1"
                )
                ct["phase"] = "choose_turn"
                room_data = game_rooms.get(room_id)
                chooser_name = room_data.host_username if ct["chooser"] == "player1" else room_data.guest_username
                for ws in active_connections.get(room_id, {}).values():
                    try:
                        await ws.send_json({
                            "type": "COIN_TOSS",
                            "phase": "result",
                            "caller": ct["caller"],
                            "caller_name": ct["caller_name"],
                            "caller_choice": choice,
                            "coin": ct["coin"],
                            "chooser": ct["chooser"],
                            "chooser_name": chooser_name,
                        })
                    except Exception:
                        pass
                continue

            if ct and message.get("type") == "COIN_TOSS_CHOOSE":
                if player != ct["chooser"]:
                    await websocket.send_json({"type": "ERROR", "message": t("coin_not_your_choose")})
                    continue
                choice = message.get("choice", "")
                if choice not in ("first", "second"):
                    await websocket.send_json({"type": "ERROR", "message": t("coin_invalid_choose")})
                    continue
                ct["turn_choice"] = choice
                ct["phase"] = "done"
                coin_toss_states.pop(room_id, None)

                # Re-fetch room in case we're in the other player's handler
                room = game_rooms.get(room_id)

                # Determine who goes first based on coin toss choice
                # Game engine always makes deck1's player "PLAYER1" (goes first)
                # We need the WS role assignment to match so turn validation works
                if ct["chooser"] == "player1":
                    first_is_host = (choice == "first")
                else:
                    first_is_host = (choice == "second")

                deck1, deck2 = (room.host_deck, room.guest_deck) if first_is_host else (room.guest_deck, room.host_deck)

                # If guest goes first, swap WS roles so game engine PLAYER1 = guest
                swapped = not first_is_host
                if swapped:
                    conns = active_connections.get(room_id, {})
                    if "player1" in conns and "player2" in conns:
                        active_connections[room_id] = {
                            "player1": conns["player2"],
                            "player2": conns["player1"],
                        }
                    # Notify both players of their actual role
                    for role, ws in active_connections.get(room_id, {}).items():
                        try:
                            await ws.send_json({"type": "ROLE_ASSIGN", "player": role})
                        except Exception:
                            pass

                env = PokemonTCG(seed=secrets.randbelow(10000), deck1=deck1, deck2=deck2, verbose=False)
                obs, reward, done, info = env.reset()
                games[room_id] = {
                    "env": env, "state": obs, "info": info,
                    "agent": None, "agent_player": None,
                }
                room.game_id = room_id
                base_state = serialize_state(obs)
                base_actions = serialize_available_actions(info["raw_available_actions"])
                await _send_state_to_players(room_id, {
                    "type": "STATE_UPDATE",
                    "state": base_state,
                    "availableActions": base_actions,
                    "turn": info["turn"].name,
                    "isChoosingCard": info.get("is_choosing_card", False),
                    "chooseCardPrompt": serialize_prompt(info.get("prompt")),
                    "autoExecuted": info.get("auto_executed", []),
                })
                continue

            # ── Game Action Messages ──
            err = manager.validate_message(message)
            if err:
                await websocket.send_json({"type": "ERROR", "message": err})
                continue

            if message["type"] == "ACTION":
                game = games.get(room_id)
                if not game:
                    await websocket.send_json({"type": "ERROR", "message": t("game_not_found")})
                    continue

                env = game["env"]
                available = game["info"]["raw_available_actions"]

                current_turn = game["info"]["turn"].name
                # Dynamically resolve player role from active_connections,
                # because coin-toss role swap mutates the dict without updating
                # each handler's local `player` variable.
                resolved_player = player
                for r, w in active_connections.get(room_id, {}).items():
                    if w is websocket:
                        resolved_player = r
                        break
                if not manager.validate_turn(resolved_player, current_turn):
                    await websocket.send_json({"type": "ERROR", "message": t("game_not_your_turn")})
                    continue

                idx = message["action_index"]
                if idx < 0 or idx >= len(available):
                    await websocket.send_json({"type": "ERROR", "message": t("game_invalid_action")})
                    continue

                action = available[idx]
                obs, reward, done, info = env.step(action)

                games[room_id]["state"] = obs
                games[room_id]["info"] = info

                update = {
                    "type": "STATE_UPDATE",
                    "state": serialize_state(obs),
                    "availableActions": serialize_available_actions(info["raw_available_actions"]),
                    "reward": reward,
                    "done": done,
                    "turn": info["turn"].name if not done else None,
                    "isChoosingCard": info.get("is_choosing_card", False),
                    "chooseCardPrompt": serialize_prompt(info.get("prompt")),
                    "autoExecuted": info.get("auto_executed", []),
                }

                if done:
                    update["winner"] = info.get("winner").name if info.get("winner") else None
                    winner_player = "player1" if info.get("winner") and info["winner"].name == "PLAYER1" else "player2"
                    import asyncio as _asyncio
                    _asyncio.create_task(_record_match_result(room_id, winner=winner_player))
                    await _send_state_to_players(room_id, update)
                    await _broadcast_state(room_id, {
                        "type": "GAME_OVER",
                        "winner": info.get("winner").name if info.get("winner") else None,
                    })
                    _cleanup_room(room_id)
                    break
                else:
                    await _send_state_to_players(room_id, update)

            elif message["type"] == "GET_STATE":
                game = games.get(room_id)
                if game:
                    env = game["env"]
                    state = serialize_state(env.gamestate)
                    filtered = _filter_state_for_player(state, player)
                    await websocket.send_json({
                        "type": "STATE_UPDATE",
                        "state": filtered,
                        "availableActions": serialize_available_actions(game["info"]["raw_available_actions"]),
                        "turn": game["info"]["turn"].name,
                    })

    except WebSocketDisconnect:
        await manager.handle_disconnect(player)
    except Exception as e:
        print(f"PvP WebSocket error: {e}")


# ============================================================================
# Run Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
