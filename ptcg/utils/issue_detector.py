"""
Issue detection for AI vs AI battle testing.

Two-layer detection strategy:
  Layer 1 (deterministic): Mathematically certain — never a false positive.
  Layer 2 (suspicious): Heuristic patterns — needs human confirmation.
"""

from __future__ import annotations

from typing import Any

from ptcg.core.enums import PlayerId
from ptcg.core.state import State
from ptcg.utils.checker import StateChecker


class EnhancedStateChecker(StateChecker):
    """Extended checker used only in test mode (enable_enhanced_check=True)."""

    def check(self, state: State) -> None:
        super().check(state)
        for player in [state.player1, state.player2]:
            self._check_total_cards(state, player)
            self._check_hp_validity(state, player)

    def _check_total_cards(self, state: State, player) -> None:
        total = (
            len(player.left) + len(player.hand) + len(player.discard)
            + len(player.prize) + len(player.active) + len(player.bench)
            + len(player.lostZone)
        )
        prizes_taken = 6 - len(player.prize)
        expected = 60 - prizes_taken
        if total != expected:
            self._add_error(state,
                f"[{player.id}] Total cards mismatch: {total} != {expected} "
                f"(deck={len(player.left)} hand={len(player.hand)} "
                f"discard={len(player.discard)} prize={len(player.prize)} "
                f"active={len(player.active)} bench={len(player.bench)} "
                f"lostZone={len(player.lostZone)})")

    def _check_hp_validity(self, state: State, player) -> None:
        for pokemon in player.active + player.bench:
            if hasattr(pokemon, "hp") and hasattr(pokemon, "maxHp"):
                if pokemon.hp <= 0:
                    self._add_error(state,
                        f"[{player.id}] {pokemon.__class__.__name__} hp={pokemon.hp} (dead in play)")
                if hasattr(pokemon, "maxHp") and pokemon.hp > pokemon.maxHp:
                    self._add_error(state,
                        f"[{player.id}] {pokemon.__class__.__name__} hp={pokemon.hp} > maxHp={pokemon.maxHp}")


class IssueDetector:
    """Heuristic detector for suspicious game patterns (Layer 2)."""

    def __init__(self):
        self.findings: list[dict[str, Any]] = []

    def detect_all(self, steps: int, damage_history: list[int],
                   llm_failures: int, cards_involved: set[str],
                   winner: PlayerId | None) -> list[dict[str, Any]]:
        self.findings = []
        self._detect_softlock(steps, damage_history)
        self._detect_zero_damage_win(winner, damage_history)
        self._detect_llm_anomaly(llm_failures)
        self._detect_rare_interaction(cards_involved)
        return self.findings

    def _detect_softlock(self, steps: int, damage_history: list[int]) -> None:
        if len(damage_history) < 20:
            return
        if all(d == 0 for d in damage_history[-20:]) and steps > 50:
            self.findings.append({"category": "softlock", "severity": "suspicious",
                "message": f"No damage dealt in last 20 steps (total: {steps})"})

    def _detect_zero_damage_win(self, winner: PlayerId | None, damage_history: list[int]) -> None:
        if winner is None or len(damage_history) <= 5:
            return
        if sum(damage_history) == 0:
            self.findings.append({"category": "zero_damage_win", "severity": "suspicious",
                "message": f"Winner {winner} dealt 0 damage — possible opponent self-defeat"})

    def _detect_llm_anomaly(self, llm_failures: int) -> None:
        if llm_failures >= 3:
            self.findings.append({"category": "llm_anomaly", "severity": "suspicious",
                "message": f"LLM agent had {llm_failures} consecutive failures"})

    def _detect_rare_interaction(self, cards_involved: set[str]) -> None:
        complex_cards = {"Mew ex", "Charizard ex", "Gardevoir ex", "Lugia VSTAR",
                         "Pidgeot ex", "Iron Hands ex", "Dragapult ex"}
        rare = cards_involved & complex_cards
        if len(rare) >= 2:
            self.findings.append({"category": "rare_interaction", "severity": "suspicious",
                "message": f"Complex interaction: {', '.join(sorted(rare))}",
                "cards": sorted(rare)})
