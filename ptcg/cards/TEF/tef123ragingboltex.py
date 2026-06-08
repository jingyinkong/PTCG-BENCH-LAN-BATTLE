"""Raging Bolt ex - TEF 123"""
from ptcg.core.action import (
    AttackAction, EvolvePokemonAction, PlayPokemonAction,
    RetreatAction, choose_card_actions
)
from ptcg.core.attack import Attack
from ptcg.core.card import PokemonCard
from ptcg.core.enums import (
    CardPosition, CardType, EnergyType, PokemonPosition,
    PokemonRule, PokemonType, Stage, SuperType
)
from ptcg.core.reducer import (
    reduce_attack_action, reduce_choose_card_actions,
    reduce_evolve_pokemon_action, reduce_play_pokemon_action,
    reduce_retreat_action
)
from ptcg.i18n import t as _t
from ptcg.utils.utils import (
    auto_end_turn, check_energy, current_player,
    move_cards, opponent_active
)


class TEF123RagingBoltex(PokemonCard):
    """Raging Bolt ex - BASIC Pokemon. HP: 240.

    Attacks:
    - Bellowing Blast: Discard hand, draw 6 cards.
    - Buster Volt: Discard basic Energy from field for 70× damage.
    """
    def __init__(self) -> None:
        super().__init__()
        self.set_name = "TEF"
        self.number = "123"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "猛雷鼓ex"
        self.hp = 240
        self.pokemonType = PokemonType.NORMAL
        self.pokemonRule = PokemonRule.NONE
        self.stage = Stage.BASIC
        self.cardType = CardType.DRAGON
        self.retreat = [CardType.COLORLESS] * 3
        self.weakness = []
        self.resistance = []
        self.evolveFrom = []
        self.prize = 2
        self.energy = []
        self.attachment = []
        self.evolved = []
        self.attacks = [
            Attack({
                "name": "飞溅咆哮",
                "damage": 0,
                "cost": [CardType.COLORLESS],
                "text": "将自己的手牌全部放于弃牌区，从牌库上方抽取6张卡牌。"
            }),
            Attack({
                "name": "极雷轰",
                "damage": 0,
                "cost": [CardType.LIGHTNING, CardType.FIGHTING],
                "text": "将自己场上宝可梦身上附着的任意数量的基本能量放于弃牌区，造成其张数x70伤害。"
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
            player = current_player(state)

            if action.attack == self.attacks[0]:
                # 飞溅咆哮: 弃掉所有手牌 → 从牌库抽6张
                hand_cards = list(player.hand)
                for card in hand_cards:
                    move_cards(
                        card,
                        (player.id, CardPosition.HAND),
                        (player.id, CardPosition.DISCARD),
                        state,
                    )
                for _ in range(6):
                    if player.left:
                        drawn = player.left[0]
                        move_cards(
                            drawn,
                            (player.id, CardPosition.LEFT),
                            (player.id, CardPosition.HAND),
                            state,
                        )
                auto_end_turn(state)

            elif action.attack == self.attacks[1]:
                # 极雷轰: 选择弃掉场上基本能量，伤害 = 弃掉数量 × 70
                all_field = [player.active] + list(player.bench) if player.active else list(player.bench)
                energy_options = []
                for pkmn in all_field:
                    for eng in pkmn.energy:
                        energy_options.append(eng)

                if energy_options:
                    tips = _t("attack.raging_bolt_ex.raging_thunder")
                    energy_actions = choose_card_actions(
                        player.id, player.id, 0, len(energy_options),
                        energy_options, tips=tips, source=self
                    )
                    chosen = yield from reduce_choose_card_actions(energy_actions, state)

                    if chosen:
                        for energy_card in chosen:
                            for pkmn in [player.active] + list(player.bench):
                                if pkmn and energy_card in pkmn.energy:
                                    pkmn.energy.remove(energy_card)
                                    player.discard.append(energy_card)
                                    break
                        action.attack.damage = len(chosen) * 70

                yield from reduce_attack_action(action, state)
                auto_end_turn(state)

            else:
                yield from reduce_attack_action(action, state)
