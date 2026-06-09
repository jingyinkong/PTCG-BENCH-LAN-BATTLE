from ptcg.core.ability import InstantAbility
"""Miraidon ex - SVI 081"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import AbilityTrigger, AbilityType, CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import check_energy, opponent_active


class SVI081Miraidonex(PokemonCard):
    """Miraidon ex - BASIC Pokemon. HP: 220."""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "SVI"
        self.number = "081"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "密勒顿ex"
        self.hp = 220
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.LIGHTNING
        self.retreat = [CardType.COLORLESS] * 1
        self.weakness = [CardType.FIGHTING]
        self.resistance = []
        self.evolveFrom = []
        self.prize = 2
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.ability = [
            InstantAbility({
                "name": "串联装置",
                "abilityType": AbilityType.INSTANT_ABILITY,
                "abilityTrigger": AbilityTrigger.OTHER,
                "onceUsedPerTurn": True,
                "text": "在自己的回合，从手牌将这张卡放置于备战区时，可使用1次。从自己的牌库选择最多2张基础【雷】宝可梦，放置于备战区。并重洗牌库。"
            })
        ]
        self.attacks = [
        Attack({"name": "光子引爆", "damage": 220, "cost": [CardType.LIGHTNING, CardType.LIGHTNING, CardType.COLORLESS], "text": "在下一个自己的回合，这只宝可梦无法使用招式。"})
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
