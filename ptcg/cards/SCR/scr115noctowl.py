from ptcg.core.ability import ActiveAbility
"""Noctowl - SCR 115"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import AbilityType, CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import check_energy, opponent_active


class SCR115Noctowl(PokemonCard):
    """Noctowl - STAGE_1 Pokemon. HP: 100."""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "SCR"
        self.number = "115"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "猫头夜鹰"
        self.hp = 100
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.STAGE_1
        self.cardType = CardType.COLORLESS
        self.retreat = [CardType.COLORLESS] * 1
        self.weakness = [CardType.LIGHTNING]
        self.resistance = [CardType.FIGHTING]
        self.evolveFrom = ['咕咕']
        self.prize = 1
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.ability = [
            ActiveAbility({
                "name": "寻找宝石",
                "abilityType": AbilityType.ACTIVE_ABILITY,
                "onceUsedPerTurn": True,
                "text": "在自己的回合可使用1次。从自己的牌库选择1张训练家卡，在给对手看过之后加入手牌。并重洗牌库。"
            })
        ]
        self.attacks = [
        Attack({"name": "高速之翼", "damage": 60, "cost": [CardType.COLORLESS, CardType.COLORLESS], "text": ""})
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
