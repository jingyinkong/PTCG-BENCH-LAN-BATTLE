"""
Monkey-patches for ptcg-engine to support PvP initial setup flow.

The upstream ptcg-engine's _run_start_stage only handles Active Pokémon selection.
This patch adds Bench Pokémon selection (0-5 cards) during the initial setup phase,
matching the official Pokémon TCG rules.
"""

from ptcg.core.envs import PokemonTCG
from ptcg.core.action import PlayPokemonAction, choose_card_actions
from ptcg.core.enums import SuperType, Stage, PokemonPosition
from ptcg.core.reducer import reduce_choose_card_actions, reduce_play_pokemon_action

_original_run_start_stage = PokemonTCG._run_start_stage


def _patched_run_start_stage(self) -> "Generator":
    """Patched start stage: choose Active (1 required) then Bench (0-5 optional)."""
    for player in [self.gamestate.player1, self.gamestate.player2]:
        self.gamestate.turn = player.id

        basic_pokemon = [
            card
            for card in player.hand
            if card.superType == SuperType.POKEMON and card.stage == Stage.BASIC
        ]

        # Step 1: Choose Active Pokémon (1 required)
        actions = choose_card_actions(
            player.id,
            player.id,
            1,
            1,
            basic_pokemon,
            tips="The game start. You should choose 1 basic Pokemon and put it onto active spot.",
        )
        pokemon = yield from reduce_choose_card_actions(actions, self.gamestate)
        reduce_play_pokemon_action(
            PlayPokemonAction(player.id, pokemon[0], PokemonPosition.ACTIVE), self.gamestate
        )

        # Step 2: Choose Bench Pokémon (0-5, optional)
        remaining_basic = [
            card
            for card in player.hand
            if card.superType == SuperType.POKEMON and card.stage == Stage.BASIC
        ]
        if remaining_basic:
            max_bench = min(5, len(remaining_basic))
            actions = choose_card_actions(
                player.id,
                player.id,
                0,
                max_bench,
                remaining_basic,
                tips="Choose up to 5 Basic Pokemon to put on your bench (optional).",
            )
            bench_pokemon = yield from reduce_choose_card_actions(actions, self.gamestate)
            for pkmn in bench_pokemon:
                reduce_play_pokemon_action(
                    PlayPokemonAction(player.id, pkmn, PokemonPosition.BENCH), self.gamestate
                )

    self.start_stage = False
    self._determine_first_player()
    self._log_game_start()


def apply_patches() -> None:
    """Apply all engine monkey-patches. Call once at startup."""
    PokemonTCG._run_start_stage = _patched_run_start_stage


def revert_patches() -> None:
    """Revert all engine monkey-patches (for testing)."""
    PokemonTCG._run_start_stage = _original_run_start_stage
