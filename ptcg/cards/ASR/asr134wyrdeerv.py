from ptcg.core.ability import InstantAbility
"""Wyrdeer V - ASR 134"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import AbilityTrigger, AbilityType, CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import check_energy, opponent_active


class ASR134WyrdeerV(PokemonCard):
    """Wyrdeer V - BASIC Pokemon. HP: 220."""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "ASR"
        self.number = "134"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "诡角鹿V"
        self.hp = 220
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.COLORLESS
        self.retreat = [CardType.COLORLESS] * 2
        self.weakness = [CardType.FIGHTING]
        self.resistance = []
        self.evolveFrom = []
        self.prize = 2
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.ability = [
            InstantAbility({
                "name": "拓荒之路",
                "abilityType": AbilityType.INSTANT_ABILITY,
                "abilityTrigger": AbilityTrigger.OTHER,
                "onceUsedPerTurn": True,
                "text": "在自己的回合，从手牌将这张卡放置于备战区时，可使用1次。从自己的牌库选择1张基本能量，附着于这只宝可梦身上。并重洗牌库。"
            })
        ]
        self.attacks = [
        Attack({"name": "屏障猛攻", "damage": 40, "cost": [CardType.COLORLESS, CardType.COLORLESS, CardType.COLORLESS], "text": "造成这只宝可梦身上附有的能量数量x40点伤害。"})
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
