"""始祖大鸟 - SIT 147"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.ability import ActiveAbility
from ptcg.core.action import UseAbilityAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import AbilityType, CardPosition, CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import check_energy, current_player, opponent_active


class SIT147Archeops(PokemonCard):
    """始祖大鸟 - STAGE_2 宝可梦。HP: 150。"""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "SIT"
        self.number = "147"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "始祖大鸟"
        self.hp = 150
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.STAGE_2
        self.cardType = CardType.COLORLESS
        self.retreat = [CardType.COLORLESS] * 1
        self.weakness = [CardType.LIGHTNING]
        self.resistance = [CardType.FIGHTING]
        self.evolveFrom = ['始祖小鸟']
        self.prize = 1
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.attacks = [
        Attack({"name": "高速之翼", "damage": 120, "cost": [CardType.COLORLESS, CardType.COLORLESS, CardType.COLORLESS], "text": ""})
        ]
        self.ability = [
        ActiveAbility({
            "name": "原始涡轮",
            "abilityType": AbilityType.ACTIVE_ABILITY,
            "onceUsedPerTurn": True,
            "text": "在自己的回合可以使用1次。选择自己牌库中最多2张特殊能量，附着于自己的1只宝可梦身上。并重洗牌库。"
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
            yield from reduce_attack_action(action, state)
        elif isinstance(action, RetreatAction):
            yield from reduce_retreat_action(action, state)

        elif isinstance(action, UseAbilityAction):
            player = current_player(state)
            player.onceUsedTurn[action.ability.name] = True
            yield None

