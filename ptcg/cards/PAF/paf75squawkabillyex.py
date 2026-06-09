from ptcg.core.ability import InstantAbility
"""Squawkabilly ex - PAF 075"""
from ptcg.core.action import (
    AttackAction, AttachEnergyAction, EvolvePokemonAction,
    PlayPokemonAction, RetreatAction, choose_card_actions
)
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import (AbilityTrigger, AbilityType,
    CardPosition, CardType, EnergyType, PokemonPosition,
    PokemonRule, PokemonType, Stage, SuperType
)
from ptcg.core.reducer import (
    reduce_attack_action, reduce_attach_energy_action,
    reduce_choose_card_actions, reduce_evolve_pokemon_action,
    reduce_play_pokemon_action, reduce_retreat_action
)
from ptcg.i18n import t as _t
from ptcg.utils.utils import (
    auto_end_turn, check_energy, current_player,
    opponent_active
)


class PAF075Squawkabillyex(PokemonCard):
    """Squawkabilly ex - BASIC Pokemon. HP: 160.

    Attack: Motivate (鼓足干劲) - Deal 20 damage, then attach up to 2 basic
    Energy from your discard pile to 1 of your Benched Pokémon.
    """
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "PAF"
        self.number = "075"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "怒鹦哥ex"
        self.hp = 160
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.COLORLESS
        self.retreat = [CardType.COLORLESS] * 1
        self.weakness = [CardType.LIGHTNING]
        self.resistance = [CardType.FIGHTING]
        self.evolveFrom = []
        self.prize = 2
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.ability = [
            InstantAbility({
                "name": "英武重抽",
                "abilityType": AbilityType.INSTANT_ABILITY,
                "abilityTrigger": AbilityTrigger.OTHER,
                "onceUsedPerTurn": True,
                "text": "在最初的自己的回合，从手牌将这张卡放置于备战区时，可使用1次。将自己的手牌全部丢到弃牌区，然后从牌库上方抽6张卡。"
            })
        ]
        self.attacks = [
            Attack({
                "name": "鼓足干劲",
                "damage": 20,
                "cost": [CardType.COLORLESS],
                "text": "选择自己弃牌区中最多2张基本能量，附着于1只备战宝可梦身上。"
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
        return actions

    def reduce_action(self, action, state):
        if isinstance(action, PlayPokemonAction):
            reduce_play_pokemon_action(action, state)
        elif isinstance(action, EvolvePokemonAction):
            reduce_evolve_pokemon_action(action, state)
        elif isinstance(action, RetreatAction):
            yield from reduce_retreat_action(action, state)
        elif isinstance(action, AttackAction):
            # 先执行基本攻击伤害(20)
            player = current_player(state)
            yield from reduce_attack_action(action, state)

            # 从弃牌区选择最多2张基本能量附着于1只备战宝可梦
            basic_energies = [
                c for c in player.discard
                if c.superType == SuperType.ENERGY
                and c.energyType == EnergyType.BASIC
            ]
            bench_pokemon = list(player.bench)

            if basic_energies and bench_pokemon:
                # 步骤1: 选择最多2张基本能量
                max_energy = min(2, len(basic_energies))
                tips = f"选择最多{max_energy}张基本能量（鼓足干劲）"
                energy_actions = choose_card_actions(
                    player.id, player.id, 0, max_energy,
                    basic_energies, tips=tips, source=self
                )
                chosen_energy = yield from reduce_choose_card_actions(
                    energy_actions, state
                )

                if chosen_energy:
                    # 步骤2: 选择1只备战宝可梦作为目标
                    tips = _t("ability.squawkabilly_ex.choose_target")
                    target_actions = choose_card_actions(
                        player.id, player.id, 1, 1,
                        bench_pokemon, tips=tips, source=self
                    )
                    chosen_target = yield from reduce_choose_card_actions(
                        target_actions, state
                    )

                    if chosen_target:
                        # 步骤3: 将能量从弃牌区移到目标宝可梦
                        for energy_card in chosen_energy:
                            if energy_card in player.discard:
                                player.discard.remove(energy_card)
                            reduce_attach_energy_action(
                                AttachEnergyAction(
                                    player.id, energy_card, chosen_target[0]
                                ),
                                state,
                                is_ability=True,
                            )

            auto_end_turn(state)
