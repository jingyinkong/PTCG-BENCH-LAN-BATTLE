#!/usr/bin/env python3
"""增强卡牌效果分类 — 对 CUSTOM 类型做关键词再分类。

用法: uv run python scripts/llm_classify_cards.py [--apply]
"""
import json
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

_ENHANCED = {
    "DAMAGE": ["AttackAction", "reduce_attack_action"],
    "SEARCH_DECK": ["search", "牌库", "choose_card_actions"],
    "DISCARD": ["discard", "丢弃"],
    "DRAW": ["抽"],
    "SWITCH": ["switch", "交换", "retreat"],
    "ATTACH_ENERGY": ["attach_energy", "附着"],
    "HEAL": ["heal", "回复"],
    "SPECIAL_CONDITION": ["SpecialCondition", "麻痹", "中毒"],
}


def classify_enhanced(card_id: str) -> str:
    from test_templates import _find_card_source
    source, _ = _find_card_source(card_id)
    if not source:
        return "CUSTOM"
    scores = {}
    for cat, kws in _ENHANCED.items():
        s = sum(1 for kw in kws if kw.lower() in source.lower())
        if s > 0: scores[cat] = s
    return max(scores, key=scores.get) if scores else "CUSTOM"


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--apply", action="store_true")
    args = p.parse_args()

    from test_templates import classify_card as base, EffectType
    cache_path = PROJECT_ROOT / "card_data_cache.json"
    cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}
    before = Counter(); after = Counter(); rec = []

    for cid in sorted(cache):
        e, _ = base(cid); before[e.name] += 1
        if e == EffectType.CUSTOM:
            nt = classify_enhanced(cid)
            after[nt] += 1
            if nt != "CUSTOM": rec.append((cid, cache[cid].get("name","?"), nt))
        else:
            after[e.name] += 1

    t = sum(before.values()); cb = before.get("CUSTOM",0); ca = after.get("CUSTOM",0)
    print(f"总卡: {t} | CUSTOM: {cb}({cb/t*100:.0f}%) -> {ca}({ca/t*100:.0f}%) | 重新分类: {len(rec)}")
    if args.apply and rec:
        for cid, _, nt in rec: cache[cid]["effect_category"] = nt
        cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"已应用: {len(rec)} 张")


if __name__ == "__main__":
    main()
