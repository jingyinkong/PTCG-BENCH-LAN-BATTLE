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
