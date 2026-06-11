"""振翼发 - PRE 043"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.ability import ActiveAbility
from ptcg.core.action import UseAbilityAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import AbilityType, CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import check_energy, current_player, opponent_active


class PRE043FlutterMane(PokemonCard):
    """振翼发 - BASIC 宝可梦。HP: 90。"""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "PRE"
        self.number = "043"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "振翼发"
        self.hp = 90
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.PSYCHIC
        self.retreat = [CardType.COLORLESS] * 1
        self.weakness = [CardType.METAL]
        self.resistance = []
        self.evolveFrom = []
        self.prize = 1
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.attacks = [
        Attack({"name": "飞来横祸", "damage": 90, "cost": [CardType.COLORLESS, CardType.COLORLESS, CardType.COLORLESS], "text": "将2个伤害指示物，以任意方式放置于对手的备战宝可梦身上。"})
        ]
        self.ability = [
        ActiveAbility({
            "name": "暗夜振翼",
            "abilityType": AbilityType.ACTIVE_ABILITY,
            "onceUsedPerTurn": False,
            "text": "只要这只宝可梦在战斗场上，对手战斗宝可梦的特性（除「暗夜振翼」外），全部消除。"
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

