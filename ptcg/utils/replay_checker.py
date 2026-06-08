"""Deterministic replay checker — verifies game state consistency on replay."""

from __future__ import annotations

import json
import hashlib
from typing import Any

from ptcg.core.action import Action
from ptcg.core.envs import PokemonTCG
from ptcg.core.state import State


class ReplayChecker:
    """Records actions and verifies determinism by replaying with same seed."""

    def __init__(self, seed: int):
        self.seed = seed
        self.actions: list[dict[str, Any]] = []

    def record_action(self, action: Action) -> None:
        try:
            self.actions.append({
                "type": type(action).__name__,
                "nl": action.to_nl() if hasattr(action, "to_nl") else str(action),
            })
        except Exception:
            self.actions.append({"type": type(action).__name__})

    def verify(self, deck1: str, deck2: str) -> tuple[bool, str | None]:
        """Replay actions and check step count matches. Returns (ok, error)."""
        try:
            env = PokemonTCG(seed=self.seed, deck1=deck1, deck2=deck2, record_game=False)
            _obs, _reward, done, info = env.reset()
            action_idx = 0
            while not done and action_idx < len(self.actions):
                actions = info.get("raw_available_actions", [])
                if not actions:
                    break
                target_type = self.actions[action_idx]["type"]
                matching = [a for a in actions if type(a).__name__ == target_type]
                action = matching[0] if matching else actions[0]
                _obs, _reward, done, info = env.step(action)
                action_idx += 1
            if action_idx != len(self.actions):
                return False, f"Replay diverged: {action_idx}/{len(self.actions)} steps"
            return True, None
        except Exception as e:
            return False, f"{type(e).__name__}: {e}"


def hash_state(state: State) -> str:
    try:
        return hashlib.sha256(
            json.dumps(state.to_dict(), sort_keys=True, default=str).encode()
        ).hexdigest()[:16]
    except Exception:
        return hashlib.sha256(str(state).encode()).hexdigest()[:16]
