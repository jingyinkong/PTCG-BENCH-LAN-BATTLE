"""Magnemite - SVI 063"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import CardPosition, CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import auto_end_turn, check_energy, current_player, move_cards, opponent_active


class SVI063Magnemite(PokemonCard):
    """Magnemite - BASIC Pokemon. HP: 60.
    Attack: Magnetic Switch - Switch with a Benched Pokemon."""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "SVI"; self.number = "063"; self.id = f"{self.set_name}-{self.number}"
        self.name = "小磁怪"; self.hp = 60
        self.pokemonType = PokemonType.NORMAL; self.pokemonRule = PokemonRule.NONE; self.stage = Stage.BASIC
        self.cardType = CardType.LIGHTNING
        self.retreat = [CardType.COLORLESS]; self.weakness = [CardType.FIGHTING]; self.resistance = []
        self.evolveFrom = []; self.prize = 1
        self.energy = []; self.attachment = []; self.evolved = []
        self.attacks = [
            Attack({"name": "互斥","damage": 0,"cost": [CardType.COLORLESS],"text": "将这只宝可梦与备战宝可梦互换。"})
        ]

    def get_actions(self, state):
        actions = []
        if self.position == PokemonPosition.ACTIVE:
            for attack in self.attacks:
                if check_energy(attack.cost, self.energy):
                    targets = opponent_active(state)
                    if targets:
                        actions.append(AttackAction(state.turn, self, attack, targets[0]))
                        break
        return actions

    def reduce_action(self, action, state):
        if isinstance(action, PlayPokemonAction): reduce_play_pokemon_action(action, state)
        elif isinstance(action, EvolvePokemonAction): reduce_evolve_pokemon_action(action, state)
        elif isinstance(action, RetreatAction): yield from reduce_retreat_action(action, state)
        elif isinstance(action, AttackAction):
            player = current_player(state)
            if action.attack.name == "互斥":
                if player.active and player.bench:
                    old = player.active[0]
                    new = player.bench[0]
                    move_cards(old, (player.id, CardPosition.ACTIVE), (player.id, CardPosition.BENCH), state)
                    move_cards(new, (player.id, CardPosition.BENCH), (player.id, CardPosition.ACTIVE), state)
                auto_end_turn(state)
            else:
                yield from reduce_attack_action(action, state)
