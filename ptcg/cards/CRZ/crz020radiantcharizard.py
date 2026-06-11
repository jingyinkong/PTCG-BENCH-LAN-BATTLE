"""光辉喷火龙 - CRZ 020"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.ability import ActiveAbility
from ptcg.core.action import UseAbilityAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import AbilityType, CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import check_energy, current_player, opponent_active


class CRZ020RadiantCharizard(PokemonCard):
    """光辉喷火龙 - BASIC 宝可梦。HP: 160。"""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "CRZ"
        self.number = "020"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "光辉喷火龙"
        self.hp = 160
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.RADIANT
        self.stage = Stage.BASIC
        self.cardType = CardType.FIRE
        self.retreat = [CardType.COLORLESS] * 3
        self.weakness = [CardType.WATER]
        self.resistance = []
        self.evolveFrom = []
        self.prize = 1
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.attacks = [
        Attack({"name": "炎爆", "damage": 250, "cost": [CardType.FIRE, CardType.COLORLESS, CardType.COLORLESS, CardType.COLORLESS, CardType.COLORLESS], "text": "在下一个自己的回合，这只宝可梦无法使用「炎爆」。"})
        ]
        self.ability = [
        ActiveAbility({
            "name": "振奋之心",
            "abilityType": AbilityType.ACTIVE_ABILITY,
            "onceUsedPerTurn": False,
            "text": "这只宝可梦使用招式所需能量会减少与对手已经获得的奖赏卡张数相同数量的【无】能量。"
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

