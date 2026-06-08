"""
Monkey-patches for ptcg-engine to support PvP initial setup flow.

The upstream ptcg-engine's _run_start_stage only handles Active Pokémon selection.
This patch adds:
1. Bench Pokémon selection (0-5 cards) during the initial setup phase
2. Mulligan rule: if a player has no Basic Pokémon, opponent draws 1 extra card,
   and the player reshuffles and redraws their hand
"""

import random

from ptcg.core.envs import PokemonTCG
from ptcg.core.player import Player
from ptcg.core.action import PlayPokemonAction, choose_card_actions
from ptcg.core.enums import SuperType, Stage, PokemonPosition, PlayerId, CardPosition
from ptcg.core.reducer import reduce_choose_card_actions, reduce_play_pokemon_action
from ptcg.i18n import t as _t

# ── Store original methods for revert ──────────────────────────────────────────
_original_run_start_stage = PokemonTCG._run_start_stage
_original_player_shuffle = Player.shuffle


# ── Patched Player.shuffle (mulligan tracking) ─────────────────────────────────

def _patched_player_shuffle(self: Player, state=None) -> None:
    """Shuffle deck and draw initial hand.

    Implements SV mulligan rule: if no Basic Pokemon in opening hand,
    reveal hand, shuffle back, and redraw. Opponent may draw 1 extra
    card per mulligan (applied later via apply_mulligan_draws).

    The _patched_run_start_stage handles Active/Bench selection and
    also serves as a safety-net mulligan check (though it should never
    trigger if shuffle's mulligan loop works correctly).

    Args:
        state: Optional State for recording mulligan auto_events.
    """
    random.shuffle(self.deck)
    self.hand = self.deck[:7]
    self.prize = self.deck[7:13]
    self.left = self.deck[13:]

    def can_play(card):
        return card.superType == SuperType.POKEMON and card.stage == Stage.BASIC

    if all(not can_play(card) for card in self.hand):
        self.mulligan_count += 1
        if state is not None:
            player_name = "PLAYER1" if self.id == PlayerId.PLAYER1 else "PLAYER2"
            state.auto_events.append(
                _t("event.mulligan_no_basic").format(
                    player=player_name, count=self.mulligan_count
                )
            )
        self.shuffle(state)

    def set_cards_position(cards, position):
        for idx, card in enumerate(cards):
            card.cardPosition = position
            card.index = idx + 1

    set_cards_position(self.hand, CardPosition.HAND)
    set_cards_position(self.prize, CardPosition.PRIZE)
    set_cards_position(self.left, CardPosition.LEFT)


# ── Patched _run_start_stage (Bench + Mulligan support) ────────────────────────

def _patched_run_start_stage(self: PokemonTCG):
    """Patched start stage: Mulligan → Choose Active (1 required) → Choose Bench (0-5)."""
    for player in [self.gamestate.player1, self.gamestate.player2]:
        self.gamestate.turn = player.id
        opponent = (
            self.gamestate.player2
            if player.id == PlayerId.PLAYER1
            else self.gamestate.player1
        )

        player_name = "Player 1" if player.id == PlayerId.PLAYER1 else "Player 2"
        opponent_name = "Player 2" if player.id == PlayerId.PLAYER1 else "Player 1"

        # ── Check for Basic Pokémon in hand ──────────────────────────────
        basic_pokemon = [
            card
            for card in player.hand
            if card.superType == SuperType.POKEMON and card.stage == Stage.BASIC
        ]

        # ── Mulligan loop: no Basic Pokémon → opponent draws extra card ──
        mulligan_count = 0
        while not basic_pokemon:
            mulligan_count += 1

            # Record mulligan event for both players to see
            self.gamestate.auto_events.append(
                _t("event.mulligan_no_basic_short").format(
                    player=player_name, opponent=opponent_name
                )
            )

            # Opponent draws 1 extra card from their deck (left pile)
            if opponent.left:
                extra_card = opponent.left.pop(0)
                opponent.hand.append(extra_card)
                # Re-index opponent's hand
                for idx, c in enumerate(opponent.hand):
                    c.index = idx + 1
                self.gamestate.auto_events.append(
                    _t("event.mulligan_opponent_draw").format(player=opponent_name)
                )

            # Player reshuffles all cards back into deck and redraws 7
            random.shuffle(player.deck)
            player.hand = player.deck[:7]
            player.prize = player.deck[7:13]
            player.left = player.deck[13:]

            # Set card positions for redrawn cards
            for idx, card in enumerate(player.hand):
                card.cardPosition = CardPosition.HAND
                card.index = idx + 1
            for idx, card in enumerate(player.prize):
                card.cardPosition = CardPosition.PRIZE
                card.index = idx + 1
            for idx, card in enumerate(player.left):
                card.cardPosition = CardPosition.LEFT
                card.index = idx + 1

            self.gamestate.auto_events.append(
                _t("event.mulligan_reshuffle").format(
                    player=player_name, count=mulligan_count
                )
            )

            # Re-check for Basic Pokémon after redraw
            basic_pokemon = [
                card
                for card in player.hand
                if card.superType == SuperType.POKEMON and card.stage == Stage.BASIC
            ]

        # ── Step 1: Choose Active Pokémon (1 required) ────────────────────
        actions = choose_card_actions(
            player.id,
            player.id,
            1,
            1,
            basic_pokemon,
            tips=_t("start.choose_active"),
        )
        pokemon = yield from reduce_choose_card_actions(actions, self.gamestate)
        reduce_play_pokemon_action(
            PlayPokemonAction(player.id, pokemon[0], PokemonPosition.ACTIVE),
            self.gamestate,
        )

        # ── Step 2: Choose Bench Pokémon (0-5, optional) ──────────────────
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
                tips=_t("start.choose_bench"),
            )
            bench_pokemon = yield from reduce_choose_card_actions(actions, self.gamestate)
            for pkmn in bench_pokemon:
                reduce_play_pokemon_action(
                    PlayPokemonAction(player.id, pkmn, PokemonPosition.BENCH),
                    self.gamestate,
                )

    self.start_stage = False
    self._determine_first_player()
    self._log_game_start()


# ── Public API ─────────────────────────────────────────────────────────────────

def apply_patches() -> None:
    """Apply all engine monkey-patches. Call once at startup."""
    Player.shuffle = _patched_player_shuffle
    PokemonTCG._run_start_stage = _patched_run_start_stage


def revert_patches() -> None:
    """Revert all engine monkey-patches (for testing)."""
    Player.shuffle = _original_player_shuffle
    PokemonTCG._run_start_stage = _original_run_start_stage
