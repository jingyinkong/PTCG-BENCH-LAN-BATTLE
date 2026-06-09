from ptcg.core.ability import PassiveAbility
"""Genesect - SFA 040"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import AbilityTrigger, AbilityType, CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import check_energy, opponent_active


class SFA040Genesect(PokemonCard):
    """Genesect - BASIC Pokemon. HP: 110."""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "SFA"
        self.number = "040"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "盖诺赛克特"
        self.hp = 110
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.METAL
        self.retreat = [CardType.COLORLESS] * 1
        self.weakness = [CardType.FIRE]
        self.resistance = [CardType.GRASS]
        self.evolveFrom = []
        self.prize = 1
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.ability = [
            PassiveAbility({
                "name": "ACE消除器",
                "abilityType": AbilityType.PASSIVE_ABILITY,
                "abilityTrigger": AbilityTrigger.OTHER,
                "onceUsedPerTurn": False,
                "text": "这只宝可梦在战斗场上时，对手无法使用ACE SPEC卡。"
            })
        ]
        self.attacks = [
        Attack({"name": "磁力爆破", "damage": 100, "cost": [CardType.METAL, CardType.COLORLESS, CardType.COLORLESS], "text": ""})
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
