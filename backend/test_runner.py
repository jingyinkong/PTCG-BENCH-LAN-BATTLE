"""
AI vs AI test runner — manages test task lifecycle and battle execution.

Reuses eval_pipeline.PipelineGameRunner for the battle loop while adding
token tracking, error collection, and issue detection on top.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth import get_current_user
from database import DB_PATH, get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/test", tags=["test"])

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class TestTaskConfig(BaseModel):
    deck_list: list[str] = ["charizard_ex"]
    agent_configs: list[dict] = []
    batch_size: int = 10
    max_budget: float | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _require_admin(user: dict) -> None:
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")


def _resolve_deck_path(deck_name: str) -> str:
    """Resolve a deck name to its full file path."""
    import ptcg.core.envs as _envs_mod

    decks_dir = Path(_envs_mod.__file__).parent.parent / "decks"
    candidate = decks_dir / f"{deck_name}.txt"
    if candidate.exists():
        return str(candidate)
    return deck_name


def _make_test_agent(agent_id: str):
    """Instantiate an agent — mirrors eval_pipeline._make_agent."""
    if agent_id == "random":
        from ptcgbench.agents.random_agent import RandomAgent
        return RandomAgent()
    if agent_id == "charizard_heuristic":
        from ptcgbench.agents.charizard_heuristic_agent import CharizardHeuristicAgent
        return CharizardHeuristicAgent()
    if ":" not in agent_id:
        raise ValueError(f"Unknown agent_id: {agent_id!r}")
    agent_type, model = agent_id.split(":", 1)
    if agent_type == "react":
        from ptcgbench.agents.react_agent import ReActAgent
        return ReActAgent(model=model)
    if agent_type == "skillevolving":
        from ptcgbench.agents.skill_evolving_agent import SkillEvolvingAgent
        return SkillEvolvingAgent(model=model)
    if agent_type == "reflexion":
        from ptcgbench.agents.reflexion_agent import ReflexionAgent
        return ReflexionAgent(model=model)
    if agent_type == "prompt_evolving":
        from ptcgbench.agents.prompt_evolving_agent import PromptEvolvingAgent
        return PromptEvolvingAgent(model=model)
    if agent_type == "expel":
        from ptcgbench.agents.expel_agent import ExpeLAgent
        return ExpeLAgent(model=model)
    if agent_type == "ltm":
        from ptcgbench.agents.ltm_agent import LTMAgent
        return LTMAgent(model=model)
    raise ValueError(f"Unknown agent type: {agent_type!r}")


def _check_llm_api_health(agent_configs: list[dict]) -> bool:
    """Quick health check: verify API key is set for each LLM agent config."""
    for cfg in agent_configs:
        if cfg.get("type") in ("random", "charizard_heuristic"):
            continue
        model = cfg.get("model", "")
        if not model:
            continue
        try:
            from ptcgbench.agents.common.model_client import build_client
            client = build_client(model)
            if not client.api_key:
                raise ValueError(f"No API key configured for model {model}")
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"LLM API health check failed for model {model}: {e}",
            )
    return True


BATTLE_TIMEOUT = 600  # 10 minutes max per battle
STEP_TIMEOUT = 120      # 2 minutes max per step (LLM API call)


class BattleTimeoutError(Exception):
    """Raised when a battle exceeds the time limit."""
    pass


def _run_battle_sync(
    p1_id: str,
    p2_id: str,
    deck: str,
    seed: int,
    max_steps: int = 500,
) -> dict:
    """Run a single battle synchronously. Called via asyncio.to_thread."""
    t_start = time.time()
    print(f"[BATTLE] seed={seed} creating agents: {p1_id} vs {p2_id}", file=sys.stderr, flush=True)
    from ptcg.core.envs import PokemonTCG
    from ptcg.core.enums import PlayerId

    p1_agent = _make_test_agent(p1_id)
    p2_agent = _make_test_agent(p2_id)
    print(f"[BATTLE] seed={seed} agents created in {time.time()-t_start:.1f}s", file=sys.stderr, flush=True)

    deck_path = _resolve_deck_path(deck)
    env = PokemonTCG(seed=seed, deck1=deck_path, deck2=deck_path, record_game=True)
    p1_agent.reset()
    p2_agent.reset()

    deck_name = Path(deck_path).stem.replace("_", "-")
    p1_name = getattr(p1_agent, "name", p1_id)
    p2_name = getattr(p2_agent, "name", p2_id)

    p1_agent.notify_game_start(deck_name, deck_name, opponent_name=p2_name)
    p2_agent.notify_game_start(deck_name, deck_name, opponent_name=p1_name)

    print(f"[BATTLE] seed={seed} resetting env...", file=sys.stderr, flush=True)
    obs, _reward, done, info = env.reset()
    print(f"[BATTLE] seed={seed} game loop starting (timeout={BATTLE_TIMEOUT}s)", file=sys.stderr, flush=True)
    steps = 0
    error_signature = None
    damage_history: list[int] = []
    llm_failures = 0
    cards_seen: set[str] = set()

    try:
        while not done and steps < max_steps:
            elapsed = time.time() - t_start
            if elapsed > BATTLE_TIMEOUT:
                raise BattleTimeoutError(
                    f"Battle timed out after {elapsed:.0f}s at step {steps}"
                )

            actions = info.get("raw_available_actions", [])
            if not actions:
                print(f"[BATTLE] seed={seed} step={steps} no actions, breaking", file=sys.stderr, flush=True)
                break

            turn: PlayerId = info.get("turn")
            step_start = time.time()
            try:
                action = (
                    p1_agent.predict(obs, info)
                    if turn == PlayerId.PLAYER1
                    else p2_agent.predict(obs, info)
                )
            except Exception as pred_err:
                print(f"[BATTLE] seed={seed} step={steps} agent predict failed: {pred_err}", file=sys.stderr, flush=True)
                error_signature = f"{type(pred_err).__name__}:{str(pred_err)[:200]}"
                break

            step_dur = time.time() - step_start
            if step_dur > STEP_TIMEOUT:
                print(f"[BATTLE] seed={seed} step={steps} SLOW ({step_dur:.1f}s)", file=sys.stderr, flush=True)

            obs, _reward, done, info = env.step(action)
            steps += 1

            if steps % 10 == 0:
                print(f"[BATTLE] seed={seed} step={steps} elapsed={elapsed:.0f}s last_step={step_dur:.1f}s", file=sys.stderr, flush=True)
    except BattleTimeoutError as e:
        error_signature = f"BattleTimeout:{str(e)[:200]}"
        print(f"[BATTLE] seed={seed} TIMEOUT: {e}", file=sys.stderr, flush=True)
    except Exception as e:
        error_signature = f"{type(e).__name__}:{str(e)[:200]}"
        print(f"[BATTLE] seed={seed} ERROR: {error_signature}", file=sys.stderr, flush=True)
    finally:
        winner = info.get("winner") or getattr(env, "winner", None)
        state = env.gamestate
        p1_prizes = len(state.player1.prize) if hasattr(state, "player1") else 0
        p2_prizes = len(state.player2.prize) if hasattr(state, "player2") else 0

        p1_result = "unknown"
        if winner == PlayerId.PLAYER1:
            p1_result = "win"
        elif winner == PlayerId.PLAYER2:
            p1_result = "loss"
        elif done:
            p1_result = "draw"

        p2_result = "win" if p1_result == "loss" else ("loss" if p1_result == "win" else p1_result)
        replay_path = env.recorder.file_path if env.recorder is not None else None

        p1_agent.post_game(result=p1_result, my_prizes=p1_prizes, opponent_prizes=p2_prizes)
        p2_agent.post_game(result=p2_result, my_prizes=p2_prizes, opponent_prizes=p1_prizes)

        if not done:
            winner_id = "draw"
        elif winner == PlayerId.PLAYER1:
            winner_id = p1_id
        elif winner == PlayerId.PLAYER2:
            winner_id = p2_id
        else:
            winner_id = "draw"

    return {
        "p1_id": p1_id,
        "p2_id": p2_id,
        "seed": seed,
        "steps": steps,
        "winner_id": winner_id,
        "error_signature": error_signature,
        "replay_path": str(replay_path) if replay_path else None,
        "state": state,
        "damage_history": damage_history,
        "llm_failures": llm_failures,
        "cards_seen": list(cards_seen),
    }


def _detect_and_save_issues(
    db: sqlite3.Connection,
    game_id: int,
    task_id: int,
    state,
    steps: int,
    damage_history: list[int],
    llm_failures: int,
    cards_seen: set[str],
    winner_id: str,
    error_signature: str | None,
) -> None:
    """Run both detection layers and save findings to detected_issues."""
    from ptcg.utils.issue_detector import EnhancedStateChecker, IssueDetector
    from ptcg.core.enums import PlayerId
    import hashlib

    try:
        state_snapshot = json.dumps(state.to_dict(), default=str)
    except Exception:
        state_snapshot = "{}"

    # Layer 1: EnhancedStateChecker (deterministic)
    try:
        checker = EnhancedStateChecker()
        checker.check(state)
    except Exception as e:
        fingerprint = hashlib.sha256(
            f"{type(e).__name__}:checker:{steps}".encode()
        ).hexdigest()[:16]
        _upsert_issue(db, game_id, task_id, "confirmed", "state_check",
                       str(e)[:500], fingerprint, state_snapshot, "[]")
        return  # Don't continue with Layer 2 if Layer 1 found a bug

    # Layer 1b: Error from battle execution
    if error_signature:
        fingerprint = hashlib.sha256(
            f"exception:{error_signature}".encode()
        ).hexdigest()[:16]
        _upsert_issue(db, game_id, task_id, "confirmed", "engine_error",
                       error_signature, fingerprint, state_snapshot, "[]")
        return

    # Layer 2: IssueDetector (suspicious patterns)
    detector = IssueDetector()
    winner = None
    if winner_id != "draw":
        try:
            winner = PlayerId[winner_id.split(":")[-1]] if ":" in winner_id else (
                PlayerId.PLAYER1 if "random" in winner_id or "charizard" in winner_id
                else PlayerId.PLAYER2)
        except (KeyError, ValueError):
            winner = PlayerId.PLAYER1

    findings = detector.detect_all(steps, damage_history, llm_failures, cards_seen, winner)
    for finding in findings:
        fingerprint = hashlib.sha256(
            f"{finding['category']}:{finding['message'][:100]}".encode()
        ).hexdigest()[:16]
        _upsert_issue(db, game_id, task_id, "suspicious", finding["category"],
                       finding["message"], fingerprint, state_snapshot, "[]")


def _upsert_issue(
    db: sqlite3.Connection,
    game_id: int,
    task_id: int,
    severity: str,
    category: str,
    error_signature: str,
    fingerprint_hash: str,
    state_snapshot: str,
    last_n_actions: str,
) -> None:
    """Insert or update an issue — increment count for same fingerprint."""
    existing = db.execute(
        "SELECT id FROM detected_issues WHERE fingerprint_hash = ? AND task_id = ?",
        (fingerprint_hash, task_id),
    ).fetchone()
    if existing:
        return  # Already recorded for this task
    db.execute(
        """INSERT INTO detected_issues
           (game_id, task_id, severity, category, error_signature,
            fingerprint_hash, state_snapshot, last_n_actions)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (game_id, task_id, severity, category, error_signature,
         fingerprint_hash, state_snapshot, last_n_actions),
    )


def _run_batch(
    task_id: int,
    deck: str,
    agent_ids: list[str],
    batch_size: int,
    base_seed: int,
) -> None:
    """Run a batch of games synchronously (called in background thread)."""
    import sys
    print(f"[BATCH] task={task_id} starting, agents={agent_ids}, deck={deck}, size={batch_size}", file=sys.stderr, flush=True)
    db = sqlite3.connect(str(DB_PATH))
    db.row_factory = sqlite3.Row

    try:
        db.execute("UPDATE test_tasks SET status = 'running' WHERE id = ?", (task_id,))
        db.commit()

        for i in range(batch_size):
            print(f"[BATCH] task={task_id} game {i+1}/{batch_size} starting...", file=sys.stderr, flush=True)
            # Rotate through agent configs for diversity
            n_agents = len(agent_ids)
            p1 = agent_ids[i % n_agents]
            p2 = agent_ids[(i + 1) % n_agents] if n_agents > 1 else agent_ids[0]
            if p1 == p2 and n_agents > 1:
                p2 = agent_ids[(i + 2) % n_agents]

            seed = base_seed + i
            result = _run_battle_sync(p1, p2, deck, seed)

            cursor = db.execute(
                """INSERT INTO test_games
                   (task_id, seed, p1_agent, p2_agent, deck, steps, winner,
                    error_signature, replay_path)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    task_id, result["seed"], result["p1_id"], result["p2_id"],
                    deck, result["steps"], result["winner_id"],
                    result["error_signature"],
                    result["replay_path"],
                ),
            )
            game_id = cursor.lastrowid
            print(f"[BATCH] task={task_id} game {i+1}/{batch_size} done: winner={result['winner_id']} steps={result['steps']}", file=sys.stderr, flush=True)

            # Run issue detection
            _detect_and_save_issues(
                db, game_id, task_id, result["state"],
                result["steps"], result["damage_history"],
                result["llm_failures"], set(result.get("cards_seen", [])),
                result["winner_id"], result["error_signature"],
            )
            db.commit()

        db.execute(
            "UPDATE test_tasks SET status = 'completed', completed_at = ? WHERE id = ?",
            (datetime.now(timezone.utc).isoformat(), task_id),
        )
        db.commit()
    except Exception as e:
        import traceback, sys
        print(f"[BATCH] task={task_id} FAILED: {e}", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
        logger.exception(f"Batch run failed for task {task_id}")
        db.execute(
            "UPDATE test_tasks SET status = 'failed', completed_at = ? WHERE id = ?",
            (datetime.now(timezone.utc).isoformat(), task_id),
        )
        db.commit()
    finally:
        db.close()


# ---------------------------------------------------------------------------
# API Routes
# ---------------------------------------------------------------------------


@router.post("/run")
async def run_test(
    config: TestTaskConfig,
    user: dict = Depends(get_current_user),
):
    """Start a new AI vs AI test run (admin only)."""
    _require_admin(user)

    # LLM API health check
    _check_llm_api_health(config.agent_configs)

    # Build agent ID strings
    agent_ids = []
    for cfg in config.agent_configs:
        atype = cfg.get("type", "random")
        model = cfg.get("model", "")
        if atype in ("random", "charizard_heuristic"):
            agent_ids.append(atype)
        else:
            agent_ids.append(f"{atype}:{model}" if model else atype)
    if not agent_ids:
        agent_ids = ["random", "random"]

    deck = config.deck_list[0] if config.deck_list else "charizard_ex"

    # Use own connection to avoid SQLite thread conflict in async handlers
    db = sqlite3.connect(str(DB_PATH))
    db.row_factory = sqlite3.Row
    try:
        cursor = db.execute(
            """INSERT INTO test_tasks
               (status, deck_list, agent_config, batch_size, max_budget, created_by)
               VALUES ('pending', ?, ?, ?, ?, ?)""",
            (
                json.dumps(config.deck_list),
                json.dumps(config.agent_configs),
                config.batch_size,
                config.max_budget,
                user["id"],
            ),
        )
        db.commit()
        task_id = cursor.lastrowid
    finally:
        db.close()

    # Run in background thread — avoid blocking FastAPI event loop
    import random
    thread = threading.Thread(
        target=_run_batch,
        args=(task_id, deck, agent_ids, config.batch_size, random.randint(0, 100000)),
        daemon=True,
    )
    thread.start()

    return {"task_id": task_id, "status": "running"}


@router.get("/tasks")
def list_tasks(
    user: dict = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
):
    """List all test tasks (admin only)."""
    _require_admin(user)
    rows = db.execute(
        "SELECT * FROM test_tasks ORDER BY created_at DESC"
    ).fetchall()

    tasks = []
    for row in rows:
        game_count = db.execute(
            "SELECT COUNT(*) FROM test_games WHERE task_id = ?", (row["id"],)
        ).fetchone()[0]

        tasks.append({
            "id": row["id"],
            "status": row["status"],
            "deck_list": json.loads(row["deck_list"]),
            "agent_config": json.loads(row["agent_config"]),
            "batch_size": row["batch_size"],
            "max_budget": row["max_budget"],
            "created_by": row["created_by"],
            "created_at": row["created_at"],
            "completed_at": row["completed_at"],
            "game_count": game_count,
        })
    return {"tasks": tasks}


@router.get("/tasks/{task_id}")
def get_task(
    task_id: int,
    user: dict = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
):
    """Get a single test task with its game results."""
    _require_admin(user)
    row = db.execute(
        "SELECT * FROM test_tasks WHERE id = ?", (task_id,)
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Task not found")

    games = db.execute(
        "SELECT * FROM test_games WHERE task_id = ? ORDER BY id",
        (task_id,),
    ).fetchall()

    return {
        "task": {
            "id": row["id"],
            "status": row["status"],
            "deck_list": json.loads(row["deck_list"]),
            "agent_config": json.loads(row["agent_config"]),
            "batch_size": row["batch_size"],
            "max_budget": row["max_budget"],
            "created_by": row["created_by"],
            "created_at": row["created_at"],
            "completed_at": row["completed_at"],
        },
        "games": [
            {
                "id": g["id"],
                "seed": g["seed"],
                "p1_agent": g["p1_agent"],
                "p2_agent": g["p2_agent"],
                "deck": g["deck"],
                "steps": g["steps"],
                "winner": g["winner"],
                "error_signature": g["error_signature"],
            }
            for g in games
        ],
    }


@router.post("/tasks/{task_id}/cancel")
def cancel_task(
    task_id: int,
    user: dict = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
):
    """Cancel a running test task."""
    _require_admin(user)
    row = db.execute("SELECT * FROM test_tasks WHERE id = ?", (task_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Task not found")
    if row["status"] not in ("pending", "running"):
        raise HTTPException(status_code=400, detail="Task is not running")

    db.execute(
        "UPDATE test_tasks SET status = 'cancelled', completed_at = ? WHERE id = ?",
        (datetime.now(timezone.utc).isoformat(), task_id),
    )
    db.commit()
    return {"status": "cancelled"}
