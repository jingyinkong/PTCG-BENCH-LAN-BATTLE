#!/usr/bin/env python3
"""比较卡牌代码实现与 tcgdex 参考数据的属性差异。"""
from __future__ import annotations
import json
from pathlib import Path
from ptcg.core.card_registry import registry
from ptcg.core.card import PokemonCard, EnergyCard, TrainerCard

PROJECT_ROOT = Path(__file__).parent.parent
REFERENCE_PATH = PROJECT_ROOT / "card_data_cache.json"
REPORT_PATH = Path(__file__).parent / "audit_report.json"


def compare_card(card, ref_data):
    diffs = []
    if ref_data.get("name") and card.name != ref_data["name"]:
        diffs.append({"field": "name", "code": card.name, "ref": ref_data["name"]})
    if isinstance(card, PokemonCard):
        if ref_data.get("hp") and card.hp != ref_data["hp"]:
            diffs.append({"field": "hp", "code": card.hp, "ref": ref_data["hp"]})
        if ref_data.get("stage"):
            ref_stage = ref_data["stage"].upper().replace(" ", "_")
            if card.stage.name != ref_stage:
                diffs.append({"field": "stage", "code": card.stage.name, "ref": ref_stage})
        if ref_data.get("retreat") is not None and len(card.retreat) != ref_data["retreat"]:
            diffs.append({"field": "retreat_count", "code": len(card.retreat), "ref": ref_data["retreat"]})
    return diffs


def main():
    registry._ensure_loaded()
    card_ids = registry.list_all()
    print(f"Comparing {len(card_ids)} cards...")
    with open(REFERENCE_PATH, encoding="utf-8") as f:
        reference = json.load(f)
    results = {}
    diffs_found = 0
    for card_id in card_ids:
        card_class = registry.get(card_id)
        if not card_class:
            continue
        try:
            card = card_class()
        except Exception as e:
            results[card_id] = {"error": str(e)}
            continue
        ref = reference.get(card_id, {})
        diffs = compare_card(card, ref)
        results[card_id] = {
            "name": card.name, "diffs": diffs,
            "has_ref": bool(ref), "verdict": "DIFF" if diffs else "OK",
        }
        if diffs:
            diffs_found += 1
    report = {
        "summary": {"total": len(results), "with_diffs": diffs_found, "ok": len(results) - diffs_found},
        "cards": results,
    }
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"Report: {REPORT_PATH}")
    print(f"Total: {len(results)}, Diffs: {diffs_found}, OK: {len(results) - diffs_found}")

if __name__ == "__main__":
    main()
