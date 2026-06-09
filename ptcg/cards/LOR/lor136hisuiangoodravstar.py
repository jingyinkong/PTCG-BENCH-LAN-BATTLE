from ptcg.core.ability import InstantAbility
"""Hisuian Goodra VSTAR - LOR 136"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import AbilityTrigger, AbilityType, CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import check_energy, opponent_active


class LOR136HisuianGoodraVSTAR(PokemonCard):
    """Hisuian Goodra VSTAR - BASIC Pokemon. HP: 270."""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "LOR"
        self.number = "136"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "洗翠 黏美龙VSTAR"
        self.hp = 270
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.DRAGON
        self.retreat = [CardType.COLORLESS] * 3
        self.weakness = []
        self.resistance = []
        self.evolveFrom = ['洗翠 黏美龙V']
        self.prize = 2
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.ability = [
            InstantAbility({
                "name": "润泽星耀",
                "abilityType": AbilityType.INSTANT_ABILITY,
                "abilityTrigger": AbilityTrigger.OTHER,
                "onceUsedPerTurn": True,
                "text": "在自己的回合可使用1次。选择自己弃牌区中的最多3张基本水能量，以任意方式附着于自己的宝可梦身上。"
            })
        ]
        self.attacks = [
        Attack({"name": "钢铁滚动", "damage": 200, "cost": [CardType.WATER, CardType.METAL, CardType.COLORLESS], "text": "在下一个对手的回合，这只宝可梦所受到的招式的伤害「-80」。"})
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
