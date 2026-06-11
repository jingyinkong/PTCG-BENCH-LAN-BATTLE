"""光辉甲贺忍蛙 - ASR 046"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.ability import ActiveAbility
from ptcg.core.action import UseAbilityAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import AbilityType, CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import check_energy, current_player, opponent_active


class ASR046RadiantGreninja(PokemonCard):
    """光辉甲贺忍蛙 - BASIC 宝可梦。HP: 130。"""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "ASR"
        self.number = "046"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "光辉甲贺忍蛙"
        self.hp = 130
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.RADIANT
        self.stage = Stage.BASIC
        self.cardType = CardType.WATER
        self.retreat = [CardType.COLORLESS] * 1
        self.weakness = [CardType.LIGHTNING]
        self.resistance = []
        self.evolveFrom = []
        self.prize = 1
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.attacks = [
        Attack({"name": "月光手里剑", "damage": 0, "cost": [CardType.WATER, CardType.WATER, CardType.COLORLESS], "text": "将附着于这只宝可梦身上的2个能量放于弃牌区，给对手的2只宝可梦，各造成90点伤害。[备战宝可梦不计算弱点、抗性。]"})
        ]
        self.ability = [
        ActiveAbility({
            "name": "隐藏牌",
            "abilityType": AbilityType.ACTIVE_ABILITY,
            "onceUsedPerTurn": True,
            "text": "在自己的回合，如果将自己手牌中的1张能量放于弃牌区的话，则可使用1次。从自己牌库上方抽取2张卡牌。"
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

