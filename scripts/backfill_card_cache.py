"""从 Python 卡牌类源码回填 card_data_cache.json 的数据空洞。

用法: uv run python scripts/backfill_card_cache.py [--dry-run]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from ptcg.core.card import EnergyCard, PokemonCard, TrainerCard
from ptcg.core.card_registry import registry

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CACHE_PATH = PROJECT_ROOT / "card_data_cache.json"


def backfill(dry_run: bool = False) -> dict:
    """回填缓存数据，返回变更统计。"""
    with open(CACHE_PATH, encoding="utf-8") as f:
        cache = json.load(f)

    stats = {
        "total": 0,
        "trainer_effect_filled": 0,
        "attack_effect_filled": 0,
        "ability_effect_filled": 0,
        "rule_box_filled": 0,
        "hp_fixed": 0,
        "retreat_fixed": 0,
        "weakness_fixed": 0,
        "resistance_fixed": 0,
        "stage_fixed": 0,
        "evolve_from_fixed": 0,
        "errors": [],
    }

    for card_id, card_data in cache.items():
        stats["total"] += 1
        try:
            cls = registry.get(card_id)
            if cls is None:
                stats["errors"].append(f"{card_id}: 未在 CardRegistry 中找到")
                continue
            inst = cls()

            # --- effect 文本 (训练家卡 & 能量卡) ---
            if isinstance(inst, (TrainerCard, EnergyCard)):
                effect_text = getattr(inst, "text", "") or ""
                current_effect = card_data.get("effect", "") or ""
                if effect_text and effect_text != current_effect:
                    card_data["effect"] = effect_text
                    stats["trainer_effect_filled"] += 1

            # --- 宝可梦 attack effects ---
            if isinstance(inst, PokemonCard):
                src_attacks = getattr(inst, "attacks", []) or []
                cache_attacks = card_data.get("attacks", []) or []

                for src_atk in src_attacks:
                    src_name = getattr(src_atk, "name", "")
                    src_text = getattr(src_atk, "text", "") or ""
                    if not src_text:
                        continue
                    for cache_atk in cache_attacks:
                        if cache_atk.get("name") == src_name:
                            if not cache_atk.get("effect", ""):
                                cache_atk["effect"] = src_text
                                stats["attack_effect_filled"] += 1
                            break

                # --- ability effects ---
                src_abilities = getattr(inst, "ability", []) or []
                cache_abilities = card_data.get("abilities", []) or []

                for src_ab in src_abilities:
                    src_name = getattr(src_ab, "name", "")
                    src_text = getattr(src_ab, "text", "") or ""
                    if not src_text:
                        continue
                    for cache_ab in cache_abilities:
                        if cache_ab.get("name") == src_name:
                            if not cache_ab.get("effect", ""):
                                cache_ab["effect"] = src_text
                                stats["ability_effect_filled"] += 1
                            if not cache_ab.get("type", ""):
                                from ptcg.core.enums import AbilityType
                                at = getattr(src_ab, "abilityType", None)
                                if at:
                                    cache_ab["type"] = at.name
                            break

                # --- rule_box ---
                if not card_data.get("rule_box", ""):
                    rule_box = _build_rule_box(inst)
                    if rule_box:
                        card_data["rule_box"] = rule_box
                        stats["rule_box_filled"] += 1

                # --- hp ---
                src_hp = getattr(inst, "hp", 0) or 0
                cache_hp = card_data.get("hp")
                if src_hp > 0 and (cache_hp is None or int(cache_hp) != src_hp):
                    card_data["hp"] = src_hp
                    stats["hp_fixed"] += 1

                # --- retreat ---
                src_retreat = [r.name for r in (getattr(inst, "retreat", []) or [])]
                if src_retreat and not card_data.get("retreat"):
                    card_data["retreat"] = len(src_retreat)
                    stats["retreat_fixed"] += 1

                # --- weakness ---
                src_weak = [w.name for w in (getattr(inst, "weakness", []) or [])]
                if src_weak and not card_data.get("weakness"):
                    card_data["weakness"] = {"type": src_weak, "value": "x2"}
                    stats["weakness_fixed"] += 1

                # --- resistance ---
                src_res = [r.name for r in (getattr(inst, "resistance", []) or [])]
                if src_res and not card_data.get("resistance"):
                    card_data["resistance"] = {"type": src_res, "value": "-30"}
                    stats["resistance_fixed"] += 1

                # --- stage ---
                src_stage = getattr(inst, "stage", None)
                if src_stage and not card_data.get("stage"):
                    card_data["stage"] = src_stage.name
                    stats["stage_fixed"] += 1

                # --- evolve_from ---
                src_evo = getattr(inst, "evolveFrom", []) or []
                if src_evo and not card_data.get("evolve_from"):
                    card_data["evolve_from"] = src_evo
                    stats["evolve_from_fixed"] += 1

        except Exception as e:
            stats["errors"].append(f"{card_id}: {e}")

    if not dry_run:
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
        print(f"已写入 {CACHE_PATH}")

    return stats


def _build_rule_box(inst: PokemonCard) -> str:
    """根据宝可梦类型构造 rule_box 文本。"""
    from ptcg.core.enums import PokemonRule, PokemonType

    rules = []
    pt = getattr(inst, "pokemonType", None)
    pr = getattr(inst, "pokemonRule", None)

    if pt == PokemonType.V:
        rules.append("宝可梦V规则: 被击倒时对方拿2张奖品卡")
    elif pt == PokemonType.VMAX:
        rules.append("宝可梦VMAX规则: 被击倒时对方拿3张奖品卡")
    elif pt == PokemonType.VSTAR:
        rules.append("宝可梦VSTAR规则: 被击倒时对方拿2张奖品卡")
    elif pt == PokemonType.EX_LOWERCASE:
        rules.append("ex规则: 被击倒时对方拿2张奖品卡")
    elif pt == PokemonType.RADIANT:
        rules.append("光辉宝可梦规则: 牌组中只能放1张光辉宝可梦")

    if pr == PokemonRule.TERA:
        rules.append("太晶: 在备战区不受攻击伤害")
    elif pr == PokemonRule.RADIANT:
        rules.append("光辉宝可梦规则: 牌组中只能放1张光辉宝可梦")

    return "; ".join(rules)


def print_stats(stats: dict) -> None:
    """打印变更统计。"""
    filled_any = (
        stats["trainer_effect_filled"]
        + stats["attack_effect_filled"]
        + stats["ability_effect_filled"]
        + stats["rule_box_filled"]
        + stats["hp_fixed"]
        + stats["retreat_fixed"]
        + stats["weakness_fixed"]
        + stats["resistance_fixed"]
        + stats["stage_fixed"]
        + stats["evolve_from_fixed"]
    )

    print(f"\n=== 回填统计 ===")
    print(f"处理卡牌总数: {stats['total']}")
    print(f"总变更数: {filled_any}")
    print(f"")
    print(f"训练家/能量 effect 补全: {stats['trainer_effect_filled']}")
    print(f"宝可梦 attack effect 补全: {stats['attack_effect_filled']}")
    print(f"宝可梦 ability effect 补全: {stats['ability_effect_filled']}")
    print(f"rule_box 补全: {stats['rule_box_filled']}")
    print(f"HP 修正: {stats['hp_fixed']}")
    print(f"撤退费用补全: {stats['retreat_fixed']}")
    print(f"弱点补全: {stats['weakness_fixed']}")
    print(f"抗性补全: {stats['resistance_fixed']}")
    print(f"阶段补全: {stats['stage_fixed']}")
    print(f"进化来源补全: {stats['evolve_from_fixed']}")

    if stats["errors"]:
        print(f"\n错误 ({len(stats['errors'])}):")
        for err in stats["errors"][:10]:
            print(f"  - {err}")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    print("模式: DRY-RUN (预览)" if dry_run else "模式: 写回")
    stats = backfill(dry_run=dry_run)
    print_stats(stats)
