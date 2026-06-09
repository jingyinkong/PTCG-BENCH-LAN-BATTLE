from ptcg.core.ability import ActiveAbility
"""Oranguru V - ASR 133"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import AbilityType, CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import check_energy, opponent_active


class ASR133OranguruV(PokemonCard):
    """Oranguru V - BASIC Pokemon. HP: 210."""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "ASR"
        self.number = "133"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "智挥猩V"
        self.hp = 210
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
            ActiveAbility({
                "name": "预订",
                "abilityType": AbilityType.ACTIVE_ABILITY,
                "onceUsedPerTurn": True,
                "text": "在自己的回合可使用1次。查看自己牌库上方3张卡，选择其中任意数量的卡加入手牌。将剩余卡放回牌库并重洗。"
            })
        ]
        self.attacks = [
        Attack({"name": "精神强念", "damage": 30, "cost": [CardType.COLORLESS, CardType.COLORLESS, CardType.COLORLESS], "text": "追加造成对手战斗宝可梦身上附有的能量数量x50点伤害。"})
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
