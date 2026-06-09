from ptcg.core.ability import PassiveAbility
"""Dusclops - SFA 019"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import AbilityTrigger, AbilityType, CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import check_energy, opponent_active


class SFA019Dusclops(PokemonCard):
    """Dusclops - STAGE_1 Pokemon. HP: 90."""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "SFA"
        self.number = "019"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "彷徨夜灵"
        self.hp = 90
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.STAGE_1
        self.cardType = CardType.PSYCHIC
        self.retreat = [CardType.COLORLESS] * 2
        self.weakness = [CardType.DARK]
        self.resistance = [CardType.FIGHTING]
        self.evolveFrom = ['夜巡灵']
        self.prize = 1
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.ability = [
            PassiveAbility({
                "name": "咒怨炸弹",
                "abilityType": AbilityType.PASSIVE_ABILITY,
                "abilityTrigger": AbilityTrigger.OTHER,
                "onceUsedPerTurn": False,
                "text": "这只宝可梦在战斗场上受到招式的伤害而昏厥时，在昏厥的宝可梦身上放置4个伤害指示物。"
            })
        ]
        self.attacks = [
        Attack({"name": "磷火", "damage": 50, "cost": [CardType.PSYCHIC, CardType.PSYCHIC], "text": ""})
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
