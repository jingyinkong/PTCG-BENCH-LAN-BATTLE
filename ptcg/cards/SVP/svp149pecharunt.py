from ptcg.core.ability import PassiveAbility
"""Pecharunt - SVP 149"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import AbilityTrigger, AbilityType, CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import check_energy, opponent_active


class SVP149Pecharunt(PokemonCard):
    """Pecharunt - BASIC Pokemon. HP: 80."""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "SVP"
        self.number = "149"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "桃歹郎"
        self.hp = 80
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.DARK
        self.retreat = [CardType.COLORLESS] * 1
        self.weakness = [CardType.FIGHTING]
        self.resistance = []
        self.evolveFrom = []
        self.prize = 1
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.ability = [
            PassiveAbility({
                "name": "剧毒支配",
                "abilityType": AbilityType.PASSIVE_ABILITY,
                "abilityTrigger": AbilityTrigger.ATTACKING,
                "onceUsedPerTurn": False,
                "text": "对手的战斗宝可梦因这只宝可梦使用招式的伤害而昏厥时，多获得1张奖赏卡。"
            })
        ]
        self.attacks = [
        Attack({"name": "毒液锁链", "damage": 10, "cost": [CardType.DARK, CardType.COLORLESS], "text": "令对手的战斗宝可梦陷入【中毒】状态。在下一个对手的回合，受到这个招式影响的宝可梦，无法撤退。"})
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
