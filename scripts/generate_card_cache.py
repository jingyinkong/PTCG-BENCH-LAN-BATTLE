#!/usr/bin/env python3
"""从 Python 卡牌源码提取游戏属性为结构化 JSON。

用法:
  uv run python scripts/generate_card_cache.py --extract                  # stdout
  uv run python scripts/generate_card_cache.py --extract --output out.json
  uv run python scripts/generate_card_cache.py --diff                     # 与缓存对比
"""
import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


def extract_all() -> dict:
    from ptcg.core.card_registry import registry
    from ptcg.core.card import (EnergyCard, ItemCard, PokemonCard,
                                 StadiumCard, SupporterCard, ToolCard)

    result = {}
    for card_id in sorted(registry.list_all()):
        try:
            cls = registry.get(card_id)
            if cls is None:
                continue
            inst = cls()
            entry = {
                "name": getattr(inst, "name", ""),
                "set_name": getattr(inst, "set_name", ""),
                "number": getattr(inst, "number", ""),
                "super_type": (inst.superType.name
                               if hasattr(inst.superType, "name")
                               else str(inst.superType)),
            }

            if isinstance(inst, PokemonCard):
                entry["card_type"] = "Pokemon"
                entry["hp"] = inst.hp
                entry["stage"] = (inst.stage.name
                                  if hasattr(inst.stage, "name") else "")
                entry["pokemon_type"] = (inst.pokemonType.name
                                         if hasattr(inst, "pokemonType") and inst.pokemonType
                                         else "")
                entry["retreat"] = [e.name for e in (inst.retreat or [])]
                if hasattr(inst, "weakness") and inst.weakness:
                    entry["weakness"] = [w.name for w in inst.weakness]
                if hasattr(inst, "resistance") and inst.resistance:
                    entry["resistance"] = [r.name for r in inst.resistance]
                entry["prize"] = getattr(inst, "prize", 0)
                entry["evolve_from"] = getattr(inst, "evolveFrom", []) or []
                src_atks = getattr(inst, "attacks", []) or []
                entry["attacks"] = [
                    {"name": a.name, "damage": a.damage if a.damage is not None else 0,
                     "cost": [c.name for c in (a.cost or [])],
                     "text": getattr(a, "text", "") or ""}
                    for a in src_atks
                ]
                src_abs = getattr(inst, "ability", []) or []
                entry["abilities"] = [
                    {"name": a.name,
                     "type": (a.abilityType.name
                              if hasattr(a, "abilityType") and a.abilityType else ""),
                     "text": getattr(a, "text", "") or ""}
                    for a in src_abs
                ]
            elif isinstance(inst, EnergyCard):
                entry["card_type"] = "Energy"
                entry["energy_type"] = (inst.energyType.name
                                        if hasattr(inst, "energyType") and inst.energyType
                                        else "")
                entry["provides"] = [e.name for e in (inst.provides or [])]
                entry["attacks"] = []
                entry["abilities"] = []
            elif isinstance(inst, (SupporterCard, ItemCard, ToolCard, StadiumCard)):
                entry["card_type"] = "Trainer"
                entry["trainer_type"] = (inst.trainerType.name
                                         if hasattr(inst, "trainerType") and inst.trainerType
                                         else "")
                entry["attacks"] = []
                entry["abilities"] = []
                if hasattr(inst, "text") and inst.text:
                    entry["effect_text"] = inst.text
            else:
                entry["card_type"] = "Unknown"
                entry["attacks"] = []
                entry["abilities"] = []

            result[card_id] = entry
        except Exception as e:
            print(f"警告: 无法提取 {card_id}: {e}", file=sys.stderr)
    return result


def main():
    p = argparse.ArgumentParser(description="从源码提取卡牌游戏属性")
    p.add_argument("--extract", action="store_true", help="提取模式")
    p.add_argument("--diff", action="store_true", help="与 card_data_cache.json 对比")
    p.add_argument("--output", help="输出文件路径")
    args = p.parse_args()

    if not args.extract and not args.diff:
        p.print_help()
        return

    if args.extract:
        data = extract_all()
        output = json.dumps(data, ensure_ascii=False, indent=2)
        if args.output:
            Path(args.output).write_text(output, encoding="utf-8")
            print(f"已提取 {len(data)} 张卡 -> {args.output}")
        else:
            print(output)

    if args.diff:
        from verify_card_consistency import run_consistency_check, format_text_report
        report = run_consistency_check()
        print(format_text_report(report))


if __name__ == "__main__":
    main()
