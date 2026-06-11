"""梦幻ex - MEW 151"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.ability import ActiveAbility
from ptcg.core.action import UseAbilityAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import AbilityType, CardPosition, CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import check_energy, current_player, opponent_active


class MEW151Mewex(PokemonCard):
    """梦幻ex - BASIC 宝可梦。HP: 180。"""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "MEW"
        self.number = "151"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "梦幻ex"
        self.hp = 180
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.PSYCHIC
        self.retreat = [CardType.COLORLESS] * 0
        self.weakness = [CardType.DARK]
        self.resistance = [CardType.FIGHTING]
        self.evolveFrom = []
        self.prize = 2
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.attacks = [
        Attack({"name": "基因侵入", "damage": 0, "cost": [CardType.COLORLESS, CardType.COLORLESS, CardType.COLORLESS], "text": "选择对手战斗宝可梦所拥有的1个招式，作为这个招式使用。"})
        ]
        self.ability = [
        ActiveAbility({
            "name": "再起动",
            "abilityType": AbilityType.ACTIVE_ABILITY,
            "onceUsedPerTurn": True,
            "text": "在自己的回合可以使用1次。从牌库上方抽取卡牌，直到自己的手牌变为3张为止。"
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

