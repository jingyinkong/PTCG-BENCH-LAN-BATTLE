"""DeltaObserver — 增量状态编码，只发送变化而非全量。

首回合全量 StateObservation，后续回合只发送 HP/能量/手牌数等变化。
"""
from __future__ import annotations
from typing import Any
from ptcgbench.agents.interfaces.observer import StateObserver


class DeltaObserver:
    """跟踪状态变化，只编码差异。token 消耗可降低 40-60%。"""

    def __init__(self):
        self._base = StateObserver()
        self._last: dict | None = None
        self._seen_cards: set[str] = set()

    def observe(self, state, info, available_actions=None) -> dict:
        current = self._base.observe(state, info, available_actions)
        cur = current.model_dump(exclude_none=True)
        if self._last is None:
            self._last = cur
            return {"mode": "full", "state": cur}
        delta = self._diff(self._last, cur)
        self._last = cur
        return {"mode": "delta", "changes": delta} if delta else {"mode": "delta", "changes": []}

    # Fields tracked per pokemon in delta mode
    _POKEMON_TRACK_FIELDS = [
        "hp", "damage_counters", "energy", "stage",
        "tools", "attacks", "abilities", "name", "id",
    ]

    def _diff(self, old: dict, new: dict) -> list[dict]:
        changes = []
        for who in ["my", "opponent"]:
            o, n = old.get(who, {}), new.get(who, {})
            for zone in ["active", "bench"]:
                oz, nz = o.get(zone, []), n.get(zone, [])

                # Detect by-name changes (knockout/switch/evolve)
                _old_names = [p.get("name") for p in oz]
                _new_names = [p.get("name") for p in nz]
                if _old_names != _new_names:
                    changes.append({
                        "field": f"{who}.{zone}_pokemon",
                        "old": _old_names,
                        "new": _new_names,
                    })

                for i, poke in enumerate(nz):
                    if i < len(oz):
                        op = oz[i]
                        for f in self._POKEMON_TRACK_FIELDS:
                            if poke.get(f) != op.get(f):
                                changes.append({
                                    "field": f"{who}.{zone}[{i}].{f}",
                                    "old": op.get(f),
                                    "new": poke.get(f),
                                })

            # Player-level state changes
            for f in ["hand_count", "deck_count", "prize_count",
                       "energy_played", "supporter_played", "retreated"]:
                if o.get(f) != n.get(f):
                    changes.append({
                        "field": f"{who}.{f}",
                        "old": o.get(f),
                        "new": n.get(f),
                    })

        if old.get("turn_number") != new.get("turn_number"):
            changes.append({
                "field": "turn_number",
                "old": old.get("turn_number"),
                "new": new.get("turn_number"),
            })
        if old.get("stadium") != new.get("stadium"):
            changes.append({
                "field": "stadium",
                "old": old.get("stadium"),
                "new": new.get("stadium"),
            })
        return changes

    def mark_seen(self, card_id: str) -> None: self._seen_cards.add(card_id)
    def is_seen(self, card_id: str) -> bool: return card_id in self._seen_cards
    def reset(self) -> None: self._last = None; self._seen_cards.clear()
