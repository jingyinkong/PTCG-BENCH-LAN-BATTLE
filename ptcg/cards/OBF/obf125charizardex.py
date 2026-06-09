from ptcg.core.ability import InstantAbility
"""Charizard ex - OBF 125"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import AbilityTrigger, AbilityType, CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import check_energy, opponent_active


class OBF125Charizardex(PokemonCard):
    """Charizard ex - STAGE_2 Pokemon. HP: 330."""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "OBF"
        self.number = "125"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "喷火龙ex"
        self.hp = 330
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.STAGE_2
        self.cardType = CardType.DARK
        self.retreat = [CardType.COLORLESS] * 2
        self.weakness = [CardType.GRASS]
        self.resistance = []
        self.evolveFrom = ['火恐龙']
        self.prize = 2
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.ability = [
            InstantAbility({
                "name": "烈炎支配",
                "abilityType": AbilityType.INSTANT_ABILITY,
                "abilityTrigger": AbilityTrigger.OTHER,
                "onceUsedPerTurn": True,
                "text": "在自己的回合，从手牌进化了这只宝可梦时，可使用1次。从自己的牌库选择最多2张基本【火】能量，附着于这只宝可梦身上。并重洗牌库。"
            })
        ]
        self.attacks = [
        Attack({"name": "燃烧黑暗", "damage": 180, "cost": [CardType.FIRE, CardType.FIRE], "text": "追加造成对手已经获得的奖赏卡张数x30伤害。"})
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
