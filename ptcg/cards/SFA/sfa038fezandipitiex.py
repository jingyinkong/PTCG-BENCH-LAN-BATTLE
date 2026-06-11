"""吉雉鸡ex - SFA 038"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.ability import ActiveAbility
from ptcg.core.action import UseAbilityAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import AbilityType, CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import check_energy, current_player, opponent_active


class SFA038Fezandipitiex(PokemonCard):
    """吉雉鸡ex - BASIC 宝可梦。HP: 210。"""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "SFA"
        self.number = "038"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "吉雉鸡ex"
        self.hp = 210
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.DARK
        self.retreat = [CardType.COLORLESS] * 1
        self.weakness = [CardType.FIGHTING]
        self.resistance = []
        self.evolveFrom = []
        self.prize = 2
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.attacks = [
        Attack({"name": "残忍箭矢", "damage": 0, "cost": [CardType.COLORLESS, CardType.COLORLESS, CardType.COLORLESS], "text": "给对手的1只宝可梦，造成100伤害。[备战宝可梦不计算弱点、抗性。]"})
        ]
        self.ability = [
        ActiveAbility({
            "name": "化危为吉",
            "abilityType": AbilityType.ACTIVE_ABILITY,
            "onceUsedPerTurn": True,
            "text": "在上一个对手的回合，如果自己的宝可梦【昏厥】的话，则在自己的回合可以使用1次。从自己牌库上方抽取3张卡牌。在这个回合，如果已经使用了其他的「化危为吉」的话，则无法使用这个特性。"
        })
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

        for ability in self.ability:
            if not current_player(state).onceUsedTurn.get(ability.name, False):
                actions.append(UseAbilityAction(state.turn, self, ability))
        return actions

    def reduce_action(self, action, state):
        if isinstance(action, PlayPokemonAction):
            reduce_play_pokemon_action(action, state)
        elif isinstance(action, EvolvePokemonAction):
            reduce_evolve_pokemon_action(action, state)
        elif isinstance(action, AttackAction):
            if action.attack == self.attacks[0]:
                            yield from reduce_attack_action(action, state)
        elif isinstance(action, RetreatAction):
            yield from reduce_retreat_action(action, state)

        elif isinstance(action, UseAbilityAction):
            player = current_player(state)
            player.onceUsedTurn[action.ability.name] = True
            yield None

