#!/usr/bin/env python3
"""PTCG 卡牌操作模式全量审计 — 分析 210 张卡 reduce_action 中的操作模式。

用法:
  uv run python scripts/audit_card_patterns.py
  uv run python scripts/audit_card_patterns.py --sample 30
  uv run python scripts/audit_card_patterns.py --output report.json

输出: .omc/state/card-pattern-audit.json
"""
import inspect
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


def extract_patterns_from_source(source: str) -> dict:
    patterns = {
        "move_cards": "move_cards" in source,
        "move_hand_to_deck": "HAND" in source and "LEFT" in source,
        "move_deck_to_hand": "LEFT" in source and "HAND" in source,
        "move_hand_to_discard": "HAND" in source and "DISCARD" in source,
        "move_discard_to_hand": "DISCARD" in source and "HAND" in source,
        "shuffle": "shuffle_cards" in source,
        "draw": "draw" in source.lower() or "抽" in source,
        "search_deck": "search" in source.lower() or "牌库" in source,
        "discard_hand": ("discard" in source.lower() and "hand" in source.lower()),
        "discard_for_cost": ("discard" in source.lower() and "其他" in source),
        "deal_damage": "damage" in source.lower() or "hp" in source.lower() or "AttackAction" in source,
        "weakness_resistance": "weakness" in source.lower() or "resistance" in source.lower(),
        "attach_energy": "attach" in source.lower() or "energy" in source.lower(),
        "switch": "switch" in source.lower() or "retreat" in source.lower(),
        "special_condition": "SpecialCondition" in source or "poison" in source.lower(),
        "heal": "heal" in source.lower() or "回复" in source,
        "choose_card": "choose_card_actions" in source,
        "flip_coin": "flip_coin" in source,
        "opponent_interact": "opponent" in source.lower() or "对手" in source,
        "conditional_prize": "prize" in source.lower(),
        "conditional_bench": "bench" in source.lower(),
        "attack_action": "AttackAction" in source,
        "item_action": "UseItemAction" in source,
        "supporter_action": "UseSupporterAction" in source,
        "ability_action": "UseAbilityAction" in source,
        "yield_from": "yield from" in source,
        "multi_step": source.count("yield") >= 2,
    }
    return {k: v for k, v in patterns.items() if v}


def audit_all(sample_size: int = 0) -> dict:
    from ptcg.core.card_registry import registry
    from ptcg.core.card import (PokemonCard, SupporterCard, ItemCard,
                                 EnergyCard, ToolCard, StadiumCard)

    all_ids = sorted(registry.list_all())
    if sample_size > 0:
        import random
        random.seed(42)
        all_ids = random.sample(all_ids, min(sample_size, len(all_ids)))

    results = {}
    pattern_freq = Counter()
    type_freq = defaultdict(Counter)

    for cid in all_ids:
        cls = registry.get(cid)
        if cls is None:
            continue
        try:
            inst = cls()
            src = inspect.getsource(type(inst).reduce_action)
        except Exception:
            continue

        active = extract_patterns_from_source(src)
        card_type = type(inst).__bases__[0].__name__

        results[cid] = {
            "name": inst.name,
            "card_type": card_type,
            "patterns": list(active.keys()),
            "pattern_count": len(active),
        }
        for p in active:
            pattern_freq[p] += 1
            type_freq[card_type][p] += 1

    return {
        "summary": {
            "total_cards": len(results),
            "avg_patterns_per_card": round(
                sum(r["pattern_count"] for r in results.values()) / max(len(results), 1), 1
            ),
        },
        "pattern_frequencies": {
            p: {"count": c, "pct": round(c / max(len(results), 1) * 100, 1)}
            for p, c in pattern_freq.most_common()
        },
        "by_card_type": {
            ct: {
                "count": sum(1 for r in results.values() if r["card_type"] == ct),
                "top_patterns": dict(freqs.most_common(10)),
            }
            for ct, freqs in type_freq.items()
        },
        "cards": results,
    }


def main():
    import argparse
    p = argparse.ArgumentParser(description="卡牌操作模式审计")
    p.add_argument("--sample", type=int, default=0, help="抽样数量")
    p.add_argument("--output", help="输出文件")
    args = p.parse_args()

    report = audit_all(args.sample)
    out_path = args.output or str(PROJECT_ROOT / ".omc" / "state" / "card-pattern-audit.json")
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    s = report["summary"]
    print(f"审计完成: {s['total_cards']} 张卡, "
          f"平均 {s['avg_patterns_per_card']} 模式/卡, "
          f"{len(report['pattern_frequencies'])} 种模式")
    print(f"\nTop 20 模式:")
    for i, (p, info) in enumerate(list(report["pattern_frequencies"].items())[:20]):
        print(f"  {i+1:2d}. {p}: {info['count']} ({info['pct']}%)")
    print(f"\n报告: {out_path}")


if __name__ == "__main__":
    main()
