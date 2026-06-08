"""Koraidon - SSP 116"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import check_energy, opponent_active


class SSP116Koraidon(PokemonCard):
    """Koraidon - BASIC Pokemon. HP: 130."""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "SSP"
        self.number = "116"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "故勒顿"
        self.hp = 130
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.FIGHTING
        self.retreat = [CardType.COLORLESS] * 2
        self.weakness = [CardType.PSYCHIC]
        self.resistance = []
        self.evolveFrom = []
        self.prize = 1
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.attacks = [
        Attack({"name": "波状猛攻", "damage": 30, "cost": [CardType.COLORLESS, CardType.COLORLESS], "text": "在上一个自己的回合，如果这只宝可梦以外的「古代」宝可梦使用了招式的话，则追加造成150伤害。"}),
        Attack({"name": "头突", "damage": 110, "cost": [CardType.FIGHTING, CardType.FIGHTING, CardType.COLORLESS], "text": ""})
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
