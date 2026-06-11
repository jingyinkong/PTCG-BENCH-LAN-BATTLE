#!/usr/bin/env python3
"""卡牌数据一致性诊断脚本 — 对比 card_data_cache.json 与 Python 卡牌源码。

用法:
  uv run python scripts/verify_card_consistency.py                    # 全量 JSON
  uv run python scripts/verify_card_consistency.py --card PAL-185     # 单卡
  uv run python scripts/verify_card_consistency.py --format text      # 文本报告
  uv run python scripts/verify_card_consistency.py --severity ERROR   # 仅 ERROR

输出: JSON DiffReport (stdout) 或文本报告
"""
import argparse
import json
import sys
from enum import Enum
from pathlib import Path
from typing import Any, Optional

PROJECT_ROOT = Path(__file__).parent.parent
CACHE_PATH = PROJECT_ROOT / "card_data_cache.json"


class Severity(str, Enum):
    ERROR = "ERROR"
    WARN = "WARN"
    INFO = "INFO"


_CACHE_TYPE_MAP: dict[str, str] = {
    "Pokemon": "POKEMON", "Pokémon": "POKEMON",
    "Trainer": "TRAINER", "Energy": "ENERGY",
}

_COST_MAP: dict[str, str] = {
    "R": "FIRE", "W": "WATER", "L": "LIGHTNING", "G": "GRASS",
    "P": "PSYCHIC", "F": "FIGHTING", "D": "DARK", "M": "METAL",
    "C": "COLORLESS",
}


def _load_cache() -> dict[str, dict]:
    if not CACHE_PATH.exists():
        print(f"警告: {CACHE_PATH} 不存在", file=sys.stderr)
        return {}
    with open(CACHE_PATH, encoding="utf-8") as f:
        return json.load(f)


def _get_source_instance(card_id: str):
    try:
        from ptcg.core.card_registry import registry
        cls = registry.get(card_id)
        if cls is None:
            return None
        return cls()
    except Exception:
        return None


def _normalize_damage(dmg: Any) -> Optional[int]:
    if dmg is None:
        return None
    if isinstance(dmg, dict):
        return dmg.get("amount", 0) or 0
    try:
        return int(dmg)
    except (ValueError, TypeError):
        return None


def _normalize_cost(cost: list) -> list[str]:
    result = []
    for c in (cost or []):
        if hasattr(c, "name"):
            result.append(c.name)
        elif isinstance(c, str):
            result.append(_COST_MAP.get(c, c))
        else:
            result.append(str(c))
    return result


def _is_pokemon_card(inst: Any) -> bool:
    return hasattr(inst, "hp") and getattr(inst, "hp", None) is not None and inst.hp > 0


def compare_card(card_id: str, cache_data: dict, inst: Any) -> list[dict]:
    diffs: list[dict] = []

    cache_name = cache_data.get("name", "")
    src_name = getattr(inst, "name", "")
    if cache_name and src_name and cache_name != src_name:
        diffs.append({"severity": "WARN", "field": "name",
                       "cache": cache_name, "source": src_name})

    cache_ct = cache_data.get("card_type", "")
    src_st = inst.superType.name if hasattr(inst.superType, "name") else str(inst.superType)
    mapped_cache = _CACHE_TYPE_MAP.get(cache_ct, cache_ct.upper() if cache_ct else "")
    if mapped_cache != src_st:
        diffs.append({"severity": "ERROR", "field": "super_type",
                       "cache": cache_ct, "source": src_st})

    if _is_pokemon_card(inst):
        cache_hp = cache_data.get("hp")
        src_hp = inst.hp
        if cache_hp is not None and src_hp is not None and int(cache_hp) != src_hp:
            diffs.append({"severity": "WARN", "field": "hp",
                           "cache": cache_hp, "source": src_hp})

    cache_atks = cache_data.get("attacks", []) or []
    src_atks = getattr(inst, "attacks", []) or []
    for i in range(max(len(cache_atks), len(src_atks))):
        prefix = f"attacks[{i}]"
        ca = cache_atks[i] if i < len(cache_atks) else None
        sa = src_atks[i] if i < len(src_atks) else None
        if ca is None:
            diffs.append({"severity": "INFO", "field": prefix,
                           "cache": None, "source": sa.name if sa else "?"})
            continue
        if sa is None:
            diffs.append({"severity": "INFO", "field": prefix,
                           "cache": ca.get("name", "?"), "source": None})
            continue
        if ca.get("name") != sa.name:
            diffs.append({"severity": "WARN", "field": f"{prefix}.name",
                           "cache": ca.get("name"), "source": sa.name})
        cache_dmg = _normalize_damage(ca.get("damage"))
        src_dmg = sa.damage if sa.damage is not None else 0
        if cache_dmg is not None and cache_dmg != src_dmg:
            diffs.append({"severity": "WARN", "field": f"{prefix}.damage",
                           "cache": cache_dmg, "source": src_dmg})
        cache_cost = _normalize_cost(ca.get("cost", []))
        src_cost = _normalize_cost(sa.cost or [])
        if cache_cost and src_cost and cache_cost != src_cost:
            diffs.append({"severity": "INFO", "field": f"{prefix}.cost",
                           "cache": cache_cost, "source": src_cost})

    cache_abs = cache_data.get("abilities", []) or []
    src_abs = getattr(inst, "ability", []) or []
    for i in range(max(len(cache_abs), len(src_abs))):
        prefix = f"abilities[{i}]"
        ca = cache_abs[i] if i < len(cache_abs) else None
        sa = src_abs[i] if i < len(src_abs) else None
        if ca is None:
            diffs.append({"severity": "INFO", "field": prefix,
                           "cache": None, "source": sa.name if sa else "?"})
            continue
        if sa is None:
            diffs.append({"severity": "INFO", "field": prefix,
                           "cache": ca.get("name", "?"), "source": None})
            continue
        if ca.get("name") != sa.name:
            diffs.append({"severity": "WARN", "field": f"{prefix}.name",
                           "cache": ca.get("name"), "source": sa.name})
        ca_type = ca.get("type", "")
        sa_type = sa.abilityType.name if hasattr(sa, "abilityType") and sa.abilityType else ""
        if ca_type and sa_type and ca_type != sa_type:
            diffs.append({"severity": "INFO", "field": f"{prefix}.type",
                           "cache": ca_type, "source": sa_type})
    return diffs


def run_consistency_check(card_ids=None, severity_filter=None):
    cache = _load_cache()
    if card_ids is None:
        card_ids = sorted(cache.keys())

    results = {}
    summary = {"total": len(card_ids), "error": 0, "warn": 0, "info": 0, "ok": 0,
               "cache_only": 0, "source_only": 0}

    for cid in card_ids:
        cache_data = cache.get(cid)
        inst = _get_source_instance(cid)
        if cache_data is None and inst is None:
            continue
        if cache_data is None:
            results[cid] = [{"severity": "INFO", "field": "_meta",
                              "cache": None, "source": inst.name,
                              "msg": "source_only: 仅源码有"}]
            summary["source_only"] += 1
            continue
        if inst is None:
            results[cid] = [{"severity": "INFO", "field": "_meta",
                              "cache": cache_data.get("name", "?"), "source": None,
                              "msg": "cache_only: 仅缓存有"}]
            summary["cache_only"] += 1
            continue

        diffs = compare_card(cid, cache_data, inst)
        if severity_filter:
            diffs = [d for d in diffs if d["severity"] == severity_filter]
        results[cid] = diffs
        if not diffs:
            summary["ok"] += 1
        else:
            for d in diffs:
                sev = d["severity"].lower()
                if sev in summary:
                    summary[sev] += 1

    by_severity = {"ERROR": [], "WARN": [], "INFO": []}
    for cid, diffs in results.items():
        for d in diffs:
            entry = dict(d)
            entry["card_id"] = cid
            by_severity.setdefault(d["severity"], []).append(entry)

    return {"summary": summary, "by_card": results, "by_severity": by_severity}


def format_text_report(report):
    lines = []
    s = report["summary"]
    lines.append("=" * 60)
    lines.append("  卡牌数据一致性诊断报告")
    lines.append("=" * 60)
    lines.append(f"  总计: {s['total']} 张卡")
    lines.append(f"  ERROR: {s['error']}  |  WARN: {s['warn']}  |  INFO: {s['info']}  |  OK: {s['ok']}")
    if s.get("cache_only", 0):
        lines.append(f"  仅缓存有: {s['cache_only']}  |  仅源码有: {s.get('source_only', 0)}")
    lines.append("=" * 60)
    for sev in ["ERROR", "WARN", "INFO"]:
        items = report["by_severity"].get(sev, [])
        if not items:
            continue
        lines.append(f"\n--- {sev} ({len(items)} 项) ---")
        for item in items[:20]:
            lines.append(f"  [{item['card_id']}] {item['field']}: "
                         f"cache={item.get('cache', '?')} → source={item.get('source', '?')}")
        if len(items) > 20:
            lines.append(f"  ... 还有 {len(items) - 20} 项")
    lines.append(f"\n{'=' * 60}")
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser(description="卡牌数据一致性诊断")
    p.add_argument("--card", help="指定卡牌 ID")
    p.add_argument("--format", choices=["json", "text"], default="json")
    p.add_argument("--severity", choices=["ERROR", "WARN", "INFO"])
    p.add_argument("--output", help="输出到文件")
    args = p.parse_args()

    card_ids = [args.card] if args.card else None
    report = run_consistency_check(card_ids, args.severity)

    output = format_text_report(report) if args.format == "text" else \
             json.dumps(report, ensure_ascii=False, indent=2)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"报告已写入: {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
