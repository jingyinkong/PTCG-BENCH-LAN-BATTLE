"""Action 工厂函数 — 统一卡牌创建 Action 对象的入口。

目的：当 Action 类的构造器签名变更时，只需修改此文件中的工厂函数，
而不是修改所有使用该 Action 的卡牌文件。这是引擎-卡牌解耦的第一步。

用法（卡牌中）:
    from ptcg.core.action_factory import make_attack, make_play_pokemon

    actions.append(make_attack(state.turn, self, attack, target))
"""

from typing import Any, List, Optional

from ptcg.core.action import (
    AttackAction,
    AttachEnergyAction,
    ChooseCardAction,
    EffectAction,
    EvolvePokemonAction,
    PlayPokemonAction,
    RetreatAction,
    UseAbilityAction,
    UseItemAction,
    UseStadiumAction,
    UseSupporterAction,
    UseToolAction,
    choose_card_actions,
)
from ptcg.core.attack import Attack
from ptcg.core.card import Card


def make_attack(turn: int, source: Card, attack: Attack, target: Any) -> AttackAction:
    """创建 AttackAction — 卡牌中最常用的 Action（149 次调用）。"""
    return AttackAction(turn, source, attack, target)


def make_play_pokemon(player_id: Any, card: Card, position: Any = None) -> PlayPokemonAction:
    """创建 PlayPokemonAction — 第二常用的 Action（63 次调用）。"""
    return PlayPokemonAction(player_id, card, position)


def make_evolve_pokemon(player_id: Any, card: Card, source: Card) -> EvolvePokemonAction:
    """创建 EvolvePokemonAction。"""
    return EvolvePokemonAction(player_id, card, source)


def make_attach_energy(turn: int, source: Card, energy: Card, target: Card) -> AttachEnergyAction:
    """创建 AttachEnergyAction。"""
    return AttachEnergyAction(turn, source, energy, target)


def make_use_item(turn: int, source: Card) -> UseItemAction:
    """创建 UseItemAction。"""
    return UseItemAction(turn, source)


def make_use_supporter(turn: int, source: Card) -> UseSupporterAction:
    """创建 UseSupporterAction。"""
    return UseSupporterAction(turn, source)


def make_use_tool(turn: int, source: Card, target: Card) -> UseToolAction:
    """创建 UseToolAction。"""
    return UseToolAction(turn, source, target)


def make_use_ability(turn: int, source: Card, ability: Any) -> UseAbilityAction:
    """创建 UseAbilityAction。"""
    return UseAbilityAction(turn, source, ability)


def make_use_stadium(turn: int, source: Card) -> UseStadiumAction:
    """创建 UseStadiumAction。"""
    return UseStadiumAction(turn, source)


def make_retreat(player_id: Any, card: Card) -> RetreatAction:
    """创建 RetreatAction。"""
    return RetreatAction(player_id, card)


def make_effect(turn: int, source: Card, effect_type: Any, target: Any = None) -> EffectAction:
    """创建 EffectAction。"""
    return EffectAction(turn, source, effect_type, target)


def make_choose_card(
    player_id: Any,
    opponent_id: Any,
    min_count: int,
    max_count: int,
    cards: List[Card],
    **kwargs,
) -> ChooseCardAction:
    """choose_card_actions() 的便捷包装。"""
    return choose_card_actions(
        player_id, opponent_id, min_count, max_count, cards, **kwargs
    )
