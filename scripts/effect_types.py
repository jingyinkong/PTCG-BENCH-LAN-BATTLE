"""14 种卡牌效果类型定义与分类逻辑。全量扫描 290 文件的实证结果。"""
from enum import Enum
from typing import List, Set
import re


class EffectType(Enum):
    DAMAGE = "DAMAGE"
    DISCARD = "DISCARD"
    SWITCH = "SWITCH"
    EVOLVE = "EVOLVE"
    SEARCH_DECK = "SEARCH_DECK"
    BENCH = "BENCH"
    ABILITY = "ABILITY"
    DRAW = "DRAW"
    ENERGY = "ENERGY"
    SPECIAL_CONDITION = "SPECIAL_CONDITION"
    TOOL = "TOOL"
    CONDITIONAL_ATTACK = "CONDITIONAL_ATTACK"
    PRIZE = "PRIZE"
    HEAL = "HEAL"


_EFFECT_KEYWORDS = {
    EffectType.DAMAGE: [r"AttackAction", r"reduce_attack_action"],
    EffectType.DISCARD: [r"discard", r"弃牌", r"弃", r"DISCARD"],
    EffectType.SWITCH: [r"switch", r"交替", r"交换", r"换位", r"RetreatAction"],
    EffectType.EVOLVE: [r"EvolvePokemonAction", r"evolve", r"进化"],
    EffectType.SEARCH_DECK: [r"search", r"牌库", r"shuffle"],
    EffectType.BENCH: [r"bench", r"备战", r"后场", r"后备"],
    EffectType.ABILITY: [r"Ability\(", r"abilityType", r"abilityTrigger"],
    EffectType.DRAW: [r"draw", r"抽牌"],
    EffectType.ENERGY: [r"EnergyCard", r"provides", r"energyType"],
    EffectType.SPECIAL_CONDITION: [r"poison", r"burn", r"sleep", r"paraly",
                                    r"confus", r"中毒", r"麻痹", r"灼伤", r"睡眠"],
    EffectType.TOOL: [r"ToolCard", r"hasAttached", r"attachedTo"],
    EffectType.CONDITIONAL_ATTACK: [r"如果", r"若.*则", r"否则", r"失败",
                                     r"fails", r"does nothing"],
    EffectType.PRIZE: [r"prize", r"奖赏", r"Prize"],
    EffectType.HEAL: [r"heal", r"回复", r"恢复"],
}


def classify_card(source: str) -> List[EffectType]:
    matched: Set[EffectType] = set()
    for effect_type, keywords in _EFFECT_KEYWORDS.items():
        for kw in keywords:
            if re.search(kw, source, re.IGNORECASE):
                matched.add(effect_type)
                break
    if EffectType.CONDITIONAL_ATTACK in matched and EffectType.DAMAGE not in matched:
        matched.discard(EffectType.CONDITIONAL_ATTACK)
    if "AttackAction" in source:
        matched.add(EffectType.DAMAGE)
    return sorted(matched, key=lambda e: e.value)
