"""卡牌测试辅助函数 — 验证卡牌属性、效果逻辑的常用工具。

被调用者: tests/cards/{SET_CODE}/test_*.py
无同名文件: tests/cards/ 目录刚创建
数据: 纯代码，不读写数据文件
"""
from typing import Any, List, Optional
from ptcg.core.card import Card, EnergyCard, PokemonCard, TrainerCard


def verify_card_base(card, expected_name, expected_set, expected_number,
                     expected_card_type, expected_super_type):
    errors = []
    if card.name != expected_name:
        errors.append(f"name: '{expected_name}' vs '{card.name}'")
    if card.set_name != expected_set:
        errors.append(f"set: '{expected_set}' vs '{card.set_name}'")
    if card.number != expected_number:
        errors.append(f"number: '{expected_number}' vs '{card.number}'")
    if card.cardType != expected_card_type:
        errors.append(f"cardType: {expected_card_type} vs {card.cardType}")
    if card.superType != expected_super_type:
        errors.append(f"superType: {expected_super_type} vs {card.superType}")
    return errors


def verify_pokemon(card, expected_hp, expected_pkm_type, expected_stage,
                   expected_retreat, expected_weakness=None, expected_resistance=None,
                   expected_prize=1, expected_evolve_from=None):
    errors = []
    if card.hp != expected_hp:
        errors.append(f"hp: {expected_hp} vs {card.hp}")
    if card.pokemonType != expected_pkm_type:
        errors.append(f"pokemonType: {expected_pkm_type} vs {card.pokemonType}")
    if card.stage != expected_stage:
        errors.append(f"stage: {expected_stage} vs {card.stage}")
    if card.retreat != expected_retreat:
        errors.append(f"retreat: {expected_retreat} vs {card.retreat}")
    if expected_weakness is not None and card.weakness != expected_weakness:
        errors.append(f"weakness: {expected_weakness} vs {card.weakness}")
    if expected_resistance is not None and card.resistance != expected_resistance:
        errors.append(f"resistance: {expected_resistance} vs {card.resistance}")
    if card.prize != expected_prize:
        errors.append(f"prize: {expected_prize} vs {card.prize}")
    if expected_evolve_from is not None and card.evolveFrom != expected_evolve_from:
        errors.append(f"evolveFrom: {expected_evolve_from} vs {card.evolveFrom}")
    return errors


def verify_attack(card, idx, expected_name, expected_damage, expected_cost):
    errors = []
    if idx >= len(card.attacks):
        errors.append(f"attack idx {idx} >= {len(card.attacks)}")
        return errors
    atk = card.attacks[idx]
    if atk.name != expected_name:
        errors.append(f"atk[{idx}].name: '{expected_name}' vs '{atk.name}'")
    if atk.damage != expected_damage:
        errors.append(f"atk[{idx}].damage: {expected_damage} vs {atk.damage}")
    if atk.cost != expected_cost:
        errors.append(f"atk[{idx}].cost: {expected_cost} vs {atk.cost}")
    return errors


def verify_energy(card, expected_energy_type, expected_provides):
    errors = []
    if card.energyType != expected_energy_type:
        errors.append(f"energyType: {expected_energy_type} vs {card.energyType}")
    if card.provides != expected_provides:
        errors.append(f"provides: {expected_provides} vs {card.provides}")
    return errors


def verify_trainer(card, expected_trainer_type):
    errors = []
    if card.trainerType != expected_trainer_type:
        errors.append(f"trainerType: {expected_trainer_type} vs {card.trainerType}")
    return errors


def assert_no_errors(errors, card_name=""):
    prefix = f"{card_name}: " if card_name else ""
    assert len(errors) == 0, f"{prefix}属性验证失败:\n" + "\n".join(f"  - {e}" for e in errors)


# =============================================================================
# 6-Layer Test Framework
# =============================================================================
# L1: Structure Check  - __init__ 属性完整性
# L2: Action Generation - get_actions() Action 类型覆盖
# L3: Action Handling   - reduce_action() isinstance 分支覆盖
# L4: Effect Logic      - 效果行为 vs 官方文本
# L5: Edge Cases        - 边界条件行为
# L6: Integration       - 卡牌间交互
# =============================================================================


def check_l1_pokemon_structure(card) -> list[str]:
    """L1: Check Pokemon-specific structure fields."""
    errors = []
    if not hasattr(card, "attacks") or not isinstance(card.attacks, list):
        errors.append("缺少 attacks 列表")
    if not hasattr(card, "energy"):
        errors.append("缺少 energy")
    if not hasattr(card, "attachment"):
        errors.append("缺少 attachment")
    return errors


def check_l1_ability_structure(card) -> list[str]:
    """L1: Check ability fields are correctly populated."""
    errors = []
    if hasattr(card, "ability") and card.ability:
        for ab in card.ability:
            if not hasattr(ab, "name") or not ab.name:
                errors.append("ability 缺少 name")
    return errors


def get_expected_actions(card) -> set[str]:
    """L2: Determine which Action types a card should generate."""
    expected = set()
    from ptcg.core.ability import ActiveAbility
    from ptcg.core.card import ItemCard, SupporterCard, StadiumCard

    if isinstance(card, ItemCard):
        expected.add("UseItemAction")
    if isinstance(card, SupporterCard):
        expected.add("UseSupporterAction")
    if isinstance(card, StadiumCard):
        expected.add("UseStadiumAction")
    if hasattr(card, "attacks") and card.attacks:
        expected.add("AttackAction")
    if hasattr(card, "ability") and card.ability:
        for ab in card.ability:
            if isinstance(ab, ActiveAbility):
                expected.add("UseAbilityAction")
                break
    if hasattr(card, "retreat") and card.retreat:
        expected.add("RetreatAction")
    return expected


def get_handled_actions(source_code: str) -> set[str]:
    """L3: Parse isinstance branches from source to find handled Action types."""
    import re
    handled = set()
    for match in re.finditer(r"isinstance\(action,\s*(\w+)\)", source_code):
        handled.add(match.group(1))
    return handled


def check_l3_handler(source_code: str, generated_actions: set) -> dict:
    """L3: Check reduce_action handles all generated Action types."""
    handled = get_handled_actions(source_code)
    unhandled = generated_actions - handled
    return {"handled": handled, "unhandled": unhandled, "passes": len(unhandled) == 0}


# Layer 4: Effect Logic Helpers
def assert_hand_size(player, expected: int, msg: str = ""):
    assert len(player.hand) == expected, f"{msg}期望手牌{expected}实际{len(player.hand)}"


def assert_bench_size(player, expected: int, msg: str = ""):
    assert len(player.bench) == expected, f"{msg}期望后排{expected}实际{len(player.bench)}"


# Layer 5: Standard Edge Case Scenarios
EDGE_CASES = [
    "empty_deck_draw", "full_bench", "first_turn_block",
    "ability_suppressed", "item_lock", "special_condition",
    "empty_discard", "insufficient_energy",
]


def classify_card_tier(card) -> int:
    """Classify card into Tier 1/2/3 based on complexity.

    Tier 1: Basic energies, simple Pokemon (no ability, pure damage)
    Tier 2: Pokemon with ability/effects, all Trainer cards
    Tier 3: V/EX/VSTAR rule-box Pokemon
    """
    from ptcg.core.ability import ActiveAbility
    from ptcg.core.card import EnergyCard, ItemCard, SupporterCard, StadiumCard
    from ptcg.core.enums import PokemonRule

    if hasattr(card, "pokemonRule") and card.pokemonRule != PokemonRule.NONE:
        return 3
    if isinstance(card, EnergyCard):
        return 1
    if isinstance(card, (ItemCard, SupporterCard, StadiumCard)):
        return 2
    has_active = False
    if hasattr(card, "ability") and card.ability:
        for ab in card.ability:
            if isinstance(ab, ActiveAbility):
                has_active = True
    has_effect = False
    if hasattr(card, "attacks") and card.attacks:
        for atk in card.attacks:
            if atk.text and atk.text.strip():
                has_effect = True
    if has_active or has_effect:
        return 2
    return 1
