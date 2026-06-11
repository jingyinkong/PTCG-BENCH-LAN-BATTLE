"""沙奈朵ex - SVI 086"""
from ptcg.core.action import AttackAction, EvolvePokemonAction, PlayPokemonAction, RetreatAction
from ptcg.core.ability import ActiveAbility
from ptcg.core.action import UseAbilityAction
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import AbilityType, CardType, PokemonPosition, PokemonRule, PokemonType, Stage
from ptcg.core.reducer import reduce_attack_action, reduce_evolve_pokemon_action, reduce_play_pokemon_action, reduce_retreat_action
from ptcg.utils.utils import check_energy, current_player, opponent_active


class SVI086Gardevoirex(PokemonCard):
    """沙奈朵ex - STAGE_2 宝可梦。HP: 310。"""
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "SVI"
        self.number = "086"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "沙奈朵ex"
        self.hp = 310
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.STAGE_2
        self.cardType = CardType.PSYCHIC
        self.retreat = [CardType.COLORLESS] * 2
        self.weakness = [CardType.DARK]
        self.resistance = [CardType.FIGHTING]
        self.evolveFrom = ['奇鲁莉安']
        self.prize = 2
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.attacks = [
        Attack({"name": "奇迹之力", "damage": 190, "cost": [CardType.PSYCHIC, CardType.PSYCHIC, CardType.COLORLESS], "text": "将这只宝可梦的特殊状态，全部恢复。"})
        ]
        self.ability = [
        ActiveAbility({
            "name": "精神拥抱",
            "abilityType": AbilityType.ACTIVE_ABILITY,
            "onceUsedPerTurn": False,
            "text": "在自己的回合可以使用任意次。选择自己弃牌区中的1张「基本【超】能量」，附着于自己的【超】宝可梦身上。然后，在被附着的宝可梦身上放置2个伤害指示物。（对会被【昏厥】的宝可梦，无法使用这个特性。）"
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

