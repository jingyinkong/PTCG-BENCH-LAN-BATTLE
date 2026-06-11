"""PTCG 效果原语引擎 — 可组合的游戏操作原子函数。

每个原语独立可测试，与现有 Generator 模式兼容。
18 个原语覆盖审计中的 80%+ 操作模式。

类别: 卡牌移动(1) / 牌库(3) / 手牌(3) / 伤害(2) / 能量(2) /
       宝可梦(2) / 状态(2) / 硬币(1) / 元操作(2)
"""
from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any, Callable, Optional, Tuple

from ptcg.core.enums import CardPosition, Coin, SpecialCondition, SuperType

if TYPE_CHECKING:
    from ptcg.core.card import Card, EnergyCard, PokemonCard
    from ptcg.core.player import Player
    from ptcg.core.state import State

StepGenerator = Any  # Generator[Tuple[State, float, bool, dict], Any, None]


# ============================================================================
# 卡牌移动
# ============================================================================

def move_cards_between(
    cards: list["Card"],
    from_zone: Tuple["PlayerId", "CardPosition"],
    to_zone: Tuple["PlayerId", "CardPosition"],
    state: "State",
    index: Optional[int] = None,
) -> None:
    """将卡牌从一个区域移动到另一个区域。"""
    from ptcg.utils.utils import move_cards as _move
    dest = (*to_zone, index) if index is not None else to_zone
    _move(cards, from_zone, dest, state)


# ============================================================================
# 牌库
# ============================================================================

def shuffle_deck(player: "Player", state: "State") -> None:
    """洗牌玩家牌库。"""
    from ptcg.utils.utils import shuffle_cards
    shuffle_cards(player.left)


def draw_cards(player: "Player", count: int, state: "State") -> None:
    """从牌库抽牌到手牌。"""
    actual = min(count, len(player.left))
    if actual > 0:
        cards = player.left[:actual]
        move_cards_between(cards, (player.id, CardPosition.LEFT),
                           (player.id, CardPosition.HAND), state)


def search_and_move(
    player: "Player",
    filter_fn: Callable[["Card"], bool],
    max_count: int,
    state: "State",
    to_hand: bool = True,
) -> StepGenerator:
    """从牌库搜索并移动卡牌（需要玩家选择）。

    Yields: 选牌提示
    """
    from ptcg.core.action import choose_card_actions
    from ptcg.core.reducer import reduce_choose_card_actions

    candidates = [c for c in player.left if filter_fn(c)]
    if not candidates:
        return
    actions = choose_card_actions(
        player.id, player.id, 0, min(max_count, len(candidates)),
        candidates, tips="选择卡牌",
    )
    chosen = yield from reduce_choose_card_actions(actions, state)
    if chosen:
        dest = CardPosition.HAND if to_hand else CardPosition.DISCARD
        move_cards_between(chosen, (player.id, CardPosition.LEFT),
                           (player.id, dest), state)


# ============================================================================
# 手牌
# ============================================================================

def return_hand_to_deck(player: "Player", state: "State") -> None:
    """手牌全部放回牌库。"""
    if player.hand:
        move_cards_between(player.hand[:], (player.id, CardPosition.HAND),
                           (player.id, CardPosition.LEFT), state)


def discard_hand(player: "Player", state: "State") -> None:
    """丢弃全部手牌。"""
    if player.hand:
        move_cards_between(player.hand[:], (player.id, CardPosition.HAND),
                           (player.id, CardPosition.DISCARD), state)


def prompt_discard_from_hand(
    player: "Player", count: int, state: "State"
) -> StepGenerator:
    """从手牌选择丢弃（需要玩家选择）。"""
    from ptcg.core.action import choose_card_actions
    from ptcg.core.reducer import reduce_choose_card_actions

    actual = min(count, len(player.hand))
    if actual <= 0:
        return
    actions = choose_card_actions(
        player.id, player.id, actual, actual,
        player.hand, tips=f"选择 {actual} 张手牌丢弃",
    )
    chosen = yield from reduce_choose_card_actions(actions, state)
    if chosen:
        move_cards_between(chosen, (player.id, CardPosition.HAND),
                           (player.id, CardPosition.DISCARD), state)


# ============================================================================
# 伤害
# ============================================================================

def apply_weakness_resistance(
    source: "PokemonCard", target: "PokemonCard", damage: int
) -> int:
    """应用弱点/抗性。返回最终伤害。"""
    RESIST = 30
    if source.cardType in (target.weakness or []):
        return damage * 2
    if source.cardType in (target.resistance or []):
        return max(0, damage - RESIST)
    return damage


def deal_damage(target: "PokemonCard", amount: int) -> bool:
    """造成伤害。返回 True 表示击倒。"""
    target.hp -= amount
    return target.hp <= 0


# ============================================================================
# 能量
# ============================================================================

def attach_energy_to_pokemon(
    target: "PokemonCard", energy_card: "EnergyCard",
    player: "Player", state: "State", is_ability: bool = False,
) -> None:
    """贴能量到宝可梦。"""
    if not is_ability:
        player.energyPlayedTurn = True
    target.energy.extend(energy_card.provides)
    pos = target.cardPosition
    if pos == CardPosition.ACTIVE:
        move_cards_between(
            energy_card, (player.id, CardPosition.HAND),
            (player.id, CardPosition.ACTIVE_ATTACHMENT, target.index), state)
    else:
        move_cards_between(
            energy_card, (player.id, CardPosition.HAND),
            (player.id, CardPosition.BENCH_ATTACHMENT, target.index), state)


def recover_energy_from_discard(
    player: "Player", target: "PokemonCard",
    filter_fn: Callable, max_count: int, state: "State",
) -> StepGenerator:
    """从弃牌区选能量贴给宝可梦。"""
    from ptcg.core.action import choose_card_actions
    from ptcg.core.reducer import reduce_choose_card_actions

    candidates = [c for c in player.discard
                  if filter_fn(c) and getattr(c, "superType", None) == SuperType.ENERGY]
    if not candidates:
        return
    actions = choose_card_actions(
        player.id, player.id, 0, min(max_count, len(candidates)),
        candidates, tips=f"选择最多 {max_count} 张能量",
    )
    chosen = yield from reduce_choose_card_actions(actions, state)
    for e in (chosen or []):
        target.energy.extend(e.provides)
        move_cards_between(e, (player.id, CardPosition.DISCARD),
                           (player.id, CardPosition.BENCH_ATTACHMENT, target.index), state)


# ============================================================================
# 宝可梦
# ============================================================================

def switch_pokemon(player: "Player", bench_idx: int) -> None:
    """出战宝可梦与备战宝可梦交换。"""
    from ptcg.utils.utils import switch_pokemon as _sw
    if player.active and 0 < bench_idx <= len(player.bench):
        _sw(player.active[0], player.bench[bench_idx - 1], player)


def prompt_choose_bench(player: "Player", state: "State") -> StepGenerator:
    """让玩家从备战区选一只宝可梦。"""
    from ptcg.core.action import choose_card_actions
    from ptcg.core.reducer import reduce_choose_card_actions
    if not player.bench:
        return
    actions = choose_card_actions(
        player.id, player.id, 1, 1, player.bench,
        tips="选择一只备战宝可梦",
    )
    chosen = yield from reduce_choose_card_actions(actions, state)
    return chosen[0] if chosen else None


# ============================================================================
# 状态
# ============================================================================

def apply_special_condition(target: "PokemonCard", condition: SpecialCondition) -> None:
    """施加特殊状态。"""
    target.specialCondition = condition


def heal(target: "PokemonCard", amount: int, max_hp: Optional[int] = None) -> int:
    """回复 HP。返回实际回复量。"""
    limit = max_hp or getattr(target, "max_hp", target.hp + amount)
    old = target.hp
    target.hp = min(target.hp + amount, limit)
    return target.hp - old


# ============================================================================
# 硬币
# ============================================================================

def flip_coin() -> Coin:
    """抛硬币。"""
    return Coin.HEAD if random.random() < 0.5 else Coin.TAIL


# ============================================================================
# 元操作
# ============================================================================

def use_and_discard_self(card: "Card", player: "Player", state: "State") -> None:
    """使用训练家卡后将自身移至弃牌区。"""
    if card in player.hand:
        move_cards_between(
            card, (player.id, CardPosition.HAND),
            (player.id, CardPosition.DISCARD), state)


def check_condition(cond: str, state: "State", player: "Player") -> bool:
    """评估游戏条件。"""
    from ptcg.utils.utils import opponent_player
    opp = opponent_player(state)
    return {
        "supporter_available": not player.supporterPlayedTurn,
        "bench_not_empty": len(player.bench) > 0,
        "deck_not_empty": len(player.left) > 0,
        "opponent_has_bench": len(opp.bench) > 0,
        "prize_more_than_opponent": len(player.prize) > len(opp.prize),
        "first_turn": getattr(player, "firstTurn", False),
    }.get(cond, False)


# ============================================================================
# 原语注册表
# ============================================================================

PRIMITIVE_REGISTRY: dict[str, Callable] = {
    "move_cards": move_cards_between,
    "shuffle_deck": shuffle_deck,
    "draw_cards": draw_cards,
    "search_deck": search_and_move,
    "return_hand_to_deck": return_hand_to_deck,
    "discard_hand": discard_hand,
    "discard_from_hand": prompt_discard_from_hand,
    "deal_damage": deal_damage,
    "apply_weakness_resistance": apply_weakness_resistance,
    "attach_energy": attach_energy_to_pokemon,
    "recover_energy": recover_energy_from_discard,
    "switch_pokemon": switch_pokemon,
    "choose_bench": prompt_choose_bench,
    "apply_special_condition": apply_special_condition,
    "heal": heal,
    "flip_coin": flip_coin,
    "use_and_discard_self": use_and_discard_self,
    "check_condition": check_condition,
}

PRIMITIVE_COUNT = len(PRIMITIVE_REGISTRY)
