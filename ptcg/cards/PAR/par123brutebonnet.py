from ptcg.core.ability import PassiveAbility
"""Brute Bonnet - PAR 123"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import AbilityTrigger, AbilityType, CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import check_energy, opponent_active


class PAR123BruteBonnet(PokemonCard):
    """Brute Bonnet - BASIC Pokemon. HP: 120."""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "PAR"
        self.number = "123"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "猛恶菇"
        self.hp = 120
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.DARK
        self.retreat = [CardType.COLORLESS] * 3
        self.weakness = [CardType.GRASS]
        self.resistance = []
        self.evolveFrom = []
        self.prize = 1
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.ability = [
            PassiveAbility({
                "name": "烈毒粉尘",
                "abilityType": AbilityType.PASSIVE_ABILITY,
                "abilityTrigger": AbilityTrigger.ATTACKING,
                "onceUsedPerTurn": False,
                "text": "对手的战斗宝可梦因这只宝可梦使用招式的伤害而昏厥时，将那只宝可梦身上附着的所有能量丢到弃牌区。"
            })
        ]
        self.attacks = [
        Attack({"name": "暴走重锤", "damage": 120, "cost": [CardType.DARK, CardType.DARK, CardType.COLORLESS], "text": "在下一个自己的回合，这只宝可梦无法使用招式。"})
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

    def use_ability(self, action, state):
        """烈毒粉尘: 对手战斗宝可梦因这只宝可梦的招式昏厥时丢弃所有能量。"""
        pass

    def reduce_action(self, action, state):
        if isinstance(action, PlayPokemonAction):
            reduce_play_pokemon_action(action, state)
        elif isinstance(action, EvolvePokemonAction):
            reduce_evolve_pokemon_action(action, state)
        elif isinstance(action, AttackAction):
            yield from reduce_attack_action(action, state)
        elif isinstance(action, RetreatAction):
            yield from reduce_retreat_action(action, state)
