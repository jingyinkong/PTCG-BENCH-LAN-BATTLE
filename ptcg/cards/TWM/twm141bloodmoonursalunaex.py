from ptcg.core.ability import PassiveAbility
"""Bloodmoon Ursaluna ex - TWM 141"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import AbilityTrigger, AbilityType, CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import check_energy, opponent_active


class TWM141BloodmoonUrsalunaex(PokemonCard):
    """Bloodmoon Ursaluna ex - BASIC Pokemon. HP: 260."""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "TWM"
        self.number = "141"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "月月熊 赫月ex"
        self.hp = 260
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.COLORLESS
        self.retreat = [CardType.COLORLESS] * 3
        self.weakness = [CardType.FIGHTING]
        self.resistance = []
        self.evolveFrom = []
        self.prize = 2
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.ability = [
            PassiveAbility({
                "name": "老练招式",
                "abilityType": AbilityType.PASSIVE_ABILITY,
                "abilityTrigger": AbilityTrigger.ATTACKING,
                "onceUsedPerTurn": False,
                "text": "对手剩余奖赏卡每为1张，这只宝可梦使用招式所需的能量就减少1个【无】。"
            })
        ]
        self.attacks = [
        Attack({"name": "血月", "damage": 240, "cost": [CardType.COLORLESS, CardType.COLORLESS, CardType.COLORLESS, CardType.COLORLESS, CardType.COLORLESS], "text": "在下一个自己的回合，这只宝可梦无法使用招式。"})
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
