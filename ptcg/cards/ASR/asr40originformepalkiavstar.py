from ptcg.core.ability import InstantAbility
"""Origin Forme Palkia VSTAR - ASR 040"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import AbilityTrigger, AbilityType, CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import check_energy, opponent_active


class ASR040OriginFormePalkiaVSTAR(PokemonCard):
    """Origin Forme Palkia VSTAR - BASIC Pokemon. HP: 280."""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "ASR"
        self.number = "040"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "起源帕路奇亚VSTAR"
        self.hp = 280
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.WATER
        self.retreat = [CardType.COLORLESS] * 2
        self.weakness = [CardType.LIGHTNING]
        self.resistance = []
        self.evolveFrom = ['起源帕路奇亚V']
        self.prize = 2
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.ability = [
            InstantAbility({
                "name": "星耀空扉",
                "abilityType": AbilityType.INSTANT_ABILITY,
                "abilityTrigger": AbilityTrigger.OTHER,
                "onceUsedPerTurn": True,
                "text": "在自己的回合，从手牌将这张卡放置于备战区时，可使用1次。从自己的牌库选择最多2张水能量，附着于这只宝可梦身上。并重洗牌库。"
            })
        ]
        self.attacks = [
        Attack({"name": "亚空潮漩", "damage": 60, "cost": [CardType.WATER, CardType.WATER], "text": "追加造成双方备战宝可梦数量x20点伤害。"})
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
