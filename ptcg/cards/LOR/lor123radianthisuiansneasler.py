"""Radiant Hisuian Sneasler - LOR 123"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import check_energy, opponent_active


class LOR123RadiantHisuianSneasler(PokemonCard):
    """Radiant Hisuian Sneasler - BASIC Pokemon. HP: 130."""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "LOR"
        self.number = "123"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "光辉洗翠 大狃拉"
        self.hp = 130
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.RADIANT
        self.stage = Stage.BASIC
        self.cardType = CardType.DARK
        self.retreat = [CardType.COLORLESS] * 1
        self.weakness = [CardType.FIGHTING]
        self.resistance = []
        self.evolveFrom = []
        self.prize = 1
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.attacks = [
        Attack({"name": "毒击", "damage": 90, "cost": [CardType.DARK, CardType.COLORLESS, CardType.COLORLESS], "text": "使对手的战斗宝可梦陷入【中毒】状态。"})
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
        if isinstance(action, PlayPokemonAction):
            reduce_play_pokemon_action(action, state)
        elif isinstance(action, EvolvePokemonAction):
            reduce_evolve_pokemon_action(action, state)
        elif isinstance(action, AttackAction):
            yield from reduce_attack_action(action, state)
        elif isinstance(action, RetreatAction):
            yield from reduce_retreat_action(action, state)
