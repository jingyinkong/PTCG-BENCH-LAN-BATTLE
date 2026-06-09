from ptcg.core.ability import ActiveAbility
"""Entei V - BRS 022"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import AbilityType, CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import check_energy, opponent_active


class BRS022EnteiV(PokemonCard):
    """Entei V - BASIC Pokemon. HP: 230."""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "BRS"
        self.number = "022"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "炎帝V"
        self.hp = 230
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.FIRE
        self.retreat = [CardType.COLORLESS] * 3
        self.weakness = [CardType.WATER]
        self.resistance = []
        self.evolveFrom = []
        self.prize = 2
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.ability = [
            ActiveAbility({
                "name": "瞬步",
                "abilityType": AbilityType.ACTIVE_ABILITY,
                "onceUsedPerTurn": True,
                "text": "在自己的回合，若这只宝可梦在战斗场上，可使用1次。从自己的牌库上方抽1张卡。在此之前，将自己的2张手牌放回牌库并重洗。"
            })
        ]
        self.attacks = [
        Attack({"name": "燃烧回旋曲", "damage": 20, "cost": [CardType.FIRE, CardType.COLORLESS], "text": "追加造成双方备战宝可梦数量x20点伤害。"})
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
