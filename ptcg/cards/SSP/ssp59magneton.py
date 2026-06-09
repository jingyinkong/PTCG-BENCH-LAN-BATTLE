from ptcg.core.ability import InstantAbility
"""Magneton - SSP 059"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import AbilityTrigger, AbilityType, CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import check_energy, opponent_active


class SSP059Magneton(PokemonCard):
    """Magneton - STAGE_1 Pokemon. HP: 100."""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "SSP"
        self.number = "059"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "三合一磁怪"
        self.hp = 100
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.STAGE_1
        self.cardType = CardType.LIGHTNING
        self.retreat = [CardType.COLORLESS] * 1
        self.weakness = [CardType.FIGHTING]
        self.resistance = []
        self.evolveFrom = ['小磁怪']
        self.prize = 1
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.ability = [
            InstantAbility({
                "name": "过量放电",
                "abilityType": AbilityType.INSTANT_ABILITY,
                "abilityTrigger": AbilityTrigger.OTHER,
                "onceUsedPerTurn": True,
                "text": "在自己的回合，从手牌进化这只宝可梦时，可使用1次。从自己的牌库选择最多2张基本雷能量，附着于这只宝可梦身上。并重洗牌库。"
            })
        ]
        self.attacks = [
        Attack({"name": "雷电球", "damage": 40, "cost": [CardType.LIGHTNING, CardType.COLORLESS], "text": ""})
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
