"""洛奇亚VSTAR - SIT 139"""
from ptcg.core.action import AttackAction, DiscardStadiumAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.ability import ActiveAbility
from ptcg.core.action import UseAbilityAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import AbilityType, CardPosition, CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import auto_end_turn, check_energy, current_player, opponent_active


class SIT139LugiaVSTAR(PokemonCard):
    """洛奇亚VSTAR - VSTAR 宝可梦。HP: 280。"""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "SIT"
        self.number = "139"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "洛奇亚VSTAR"
        self.hp = 280
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.VSTAR
        self.cardType = CardType.COLORLESS
        self.retreat = [CardType.COLORLESS] * 2
        self.weakness = [CardType.LIGHTNING]
        self.resistance = [CardType.FIGHTING]
        self.evolveFrom = ['洛奇亚V']
        self.prize = 2
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.attacks = [
        Attack({"name": "风暴俯冲", "damage": 220, "cost": [CardType.COLORLESS, CardType.COLORLESS, CardType.COLORLESS, CardType.COLORLESS], "text": "若希望，可将场上的竞技场放于弃牌区。"})
        ]
        self.ability = [
        ActiveAbility({
            "name": "星耀汇聚",
            "abilityType": AbilityType.ACTIVE_ABILITY,
            "onceUsedPerTurn": True,
            "text": "在自己的回合可以使用。选择自己弃牌区中最多2张【无】宝可梦（除「拥有规则的宝可梦」外），放于备战区。[对战中，己方的【VSTAR】力量只能使用1次。]"
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
                yield from reduce_attack_action(action, state, auto_end_turn=False)
                player = current_player(state)
                if len(state.stadium) > 0:
                    old_stadium = state.stadium[0]
                    old_stadium.reduce_action(DiscardStadiumAction(player.id, old_stadium), state)
                auto_end_turn(state)
        elif isinstance(action, RetreatAction):
            yield from reduce_retreat_action(action, state)

        elif isinstance(action, UseAbilityAction):
            player = current_player(state)
            player.onceUsedTurn[action.ability.name] = True
            yield None

