from ptcg.core.ability import PassiveAbility
"""Pikachu ex - ASC 057"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import AbilityTrigger, AbilityType, CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import check_energy, opponent_active


class ASC057Pikachuex(PokemonCard):
    """Pikachu ex - BASIC Pokemon. HP: 200."""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "ASC"
        self.number = "057"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "皮卡丘ex"
        self.hp = 200
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
            PassiveAbility({
                "name": "顽强之心",
                "abilityType": AbilityType.PASSIVE_ABILITY,
                "abilityTrigger": AbilityTrigger.ATTACKED,
                "onceUsedPerTurn": False,
                "text": "这只宝可梦的HP是全满的状态下，因招式的伤害而将气绝时，不会气绝，而是HP以剩余「10」的状态留于战斗场上。"
            })
        ]
        self.attacks = [
        Attack({"name": "黄晶伏特", "damage": 300, "cost": [CardType.GRASS, CardType.LIGHTNING, CardType.METAL], "text": "选择这只宝可梦身上附着的3个能量，放于弃牌区。"})
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
