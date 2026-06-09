"""L4 效果逻辑验证 — 对比 tcg.mik.moe 官方数据与代码实现.

用法: uv run python scripts/verify_card_effects.py
输出: .omc/state/card-effect-verification.json
"""
import ast
import json
import re
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).parent.parent
CARDS_DIR = PROJECT_ROOT / "ptcg" / "cards"
CACHE_FILE = PROJECT_ROOT / "card_data_cache.json"
OUTPUT_FILE = PROJECT_ROOT / ".omc" / "state" / "card-effect-verification.json"

# 已知缓存数据误报：缓存中数据与代码实现不一致，但代码实现正确
# 原因：中英文重复条目 / 卡牌编号冲突（Trainer 被缓存误标为 Pokemon）
KNOWN_CACHE_FALSE_POSITIVES: set[str] = {
    "SVI-253",  # 密勒顿ex: 缓存2招，代码正确: 1招+1特性
    "PAR-086",  # 吼叫尾: 缓存招式数据重复
    "TWM-154",  # Trainer Kieran, 缓存误标为 Pokemon 吉雉鸡
}


def load_cache() -> dict:
    with open(CACHE_FILE, encoding="utf-8") as f:
        return json.load(f)


def _get_node_source(source: str, node: ast.AST) -> str:
    if hasattr(node, "lineno") and hasattr(node, "end_lineno"):
        lines = source.split("\n")
        return "\n".join(lines[node.lineno - 1:node.end_lineno])
    return ""


def _extract_str(source: str, pattern: str) -> str | None:
    m = re.search(pattern, source)
    return m.group(1) if m else None


def _extract_int(source: str, pattern: str) -> int | None:
    m = re.search(pattern, source)
    return int(m.group(1)) if m else None


def extract_code_info(filepath: Path) -> dict | None:
    try:
        source = filepath.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (SyntaxError, UnicodeDecodeError):
        return None

    card_class = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for base in node.bases:
                base_name = base.id if isinstance(base, ast.Name) else (
                    base.attr if isinstance(base, ast.Attribute) else ""
                )
                if base_name in ("PokemonCard", "EnergyCard", "SpecialEnergyCard",
                                 "ItemCard", "SupporterCard", "StadiumCard", "ToolCard"):
                    card_class = node
                    break

    if card_class is None:
        return None

    init_node = next((n for n in ast.iter_child_nodes(card_class)
                      if isinstance(n, ast.FunctionDef) and n.name == "__init__"), None)
    if init_node is None:
        return None

    init_source = _get_node_source(source, init_node)

    return {
        "file": str(filepath.relative_to(CARDS_DIR)),
        "hp": _extract_int(init_source, r'self\.hp\s*=\s*(\d+)'),
        "set_name": _extract_str(init_source, r'self\.set_name\s*=\s*"([^"]+)"'),
        "number": _extract_str(init_source, r'self\.number\s*=\s*"([^"]+)"'),
        "attacks": _extract_attacks(init_source),
        "abilities": _extract_abilities(init_source),
    }


def _extract_attacks(init_source: str) -> list[dict]:
    attacks = []
    for m in re.finditer(r'Attack\(\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}\s*\)', init_source, re.DOTALL):
        block = m.group(1)
        name = _extract_str(block, r'"name"\s*:\s*"([^"]+)"')
        damage = _extract_int(block, r'"damage"\s*:\s*(\d+)')
        text = _extract_str(block, r'"text"\s*:\s*"([^"]*)"')
        if name:
            attacks.append({"name": name, "damage": damage or 0, "text": text or ""})
    return attacks


def _extract_abilities(init_source: str) -> list[dict]:
    abilities = []
    for m in re.finditer(
        r'(ActiveAbility|PassiveAbility|InstantAbility)\s*\(\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}\s*\)',
        init_source, re.DOTALL
    ):
        atype, block = m.group(1), m.group(2)
        name = _extract_str(block, r'"name"\s*:\s*"([^"]+)"')
        text = _extract_str(block, r'"text"\s*:\s*"([^"]*)"')
        if name:
            abilities.append({"type": atype, "name": name, "text": text or ""})
    return abilities


def compare_card(code_info: dict, cache_entry: dict) -> dict:
    issues = []
    critical_count = 0
    warning_count = 0
    info_count = 0

    # HP check (WARNING)
    chp = cache_entry.get("hp")
    ohp = code_info.get("hp")
    if chp and ohp and chp != ohp:
        issues.append({"severity": "WARNING", "msg": f"HP: code={ohp} cache={chp}"})
        warning_count += 1

    # Attacks — compare by position (code=EN, cache=CN)
    # 跳过已知缓存误报
    card_id = f"{code_info.get('set_name', '?')}-{code_info.get('number', '?')}"
    if card_id in KNOWN_CACHE_FALSE_POSITIVES:
        return {
            "card_id": card_id,
            "file": code_info.get("file", "?"),
            "name": cache_entry.get("name", "?"),
            "issues": [],
            "passes": True,
            "issue_count": 0,
            "critical_count": 0,
            "warning_count": 0,
            "info_count": 0,
        }

    ca = cache_entry.get("attacks", [])
    oa = code_info.get("attacks", [])
    if len(ca) != len(oa):
        sev = "CRITICAL" if len(ca) > len(oa) else "WARNING"
        issues.append({"severity": sev,
                       "msg": f"Attack count: code={len(oa)} cache={len(ca)}"})
        if len(ca) > len(oa):
            critical_count += 1
        else:
            warning_count += 1

    for i in range(min(len(ca), len(oa))):
        atk = ca[i]
        oatk = oa[i]
        cdmg = atk.get("damage", {})
        dmg_val = cdmg.get("amount", 0) if isinstance(cdmg, dict) else (cdmg or 0)
        code_dmg = oatk.get("damage", 0)
        if dmg_val != code_dmg and not (code_dmg == 0 and dmg_val > 0):
            issues.append({"severity": "WARNING",
                           "msg": f"Atk[{i}] dmg: code={code_dmg} cache={dmg_val}"})
            warning_count += 1
        # Effect text comparison: cache has effect, code doesn't
        cache_effect = atk.get("effect", "")
        code_text = oatk.get("text", "")
        if cache_effect and not code_text:
            issues.append({"severity": "CRITICAL",
                           "msg": f"Atk[{i}] '{atk.get('name','?')}': effect in cache but MISSING in code: '{cache_effect[:60]}...'"})
            critical_count += 1

    # Abilities — check missing implementations
    cab = cache_entry.get("abilities", [])
    oab = code_info.get("abilities", [])
    if len(cab) > len(oab):
        for i in range(len(oab), len(cab)):
            issues.append({"severity": "CRITICAL",
                           "msg": f"Ability[{i}] MISSING in code: '{cab[i].get('name','?')}'"})
            critical_count += 1
    elif len(cab) < len(oab):
        issues.append({"severity": "INFO",
                       "msg": f"Ability surplus: code={len(oab)} cache={len(cab)}"})
        info_count += 1

    return {
        "card_id": f"{code_info.get('set_name', '?')}-{code_info.get('number', '?')}",
        "file": code_info.get("file", "?"),
        "name": cache_entry.get("name", "?"),
        "issues": issues,
        "passes": len(issues) == 0,
        "issue_count": len(issues),
        "critical_count": critical_count,
        "warning_count": warning_count,
        "info_count": info_count,
    }


def main():
    print("加载缓存...")
    cache = load_cache()
    print(f"解析代码...")
    code_cards = {}
    for py_file in sorted(CARDS_DIR.rglob("*.py")):
        if py_file.name == "__init__.py":
            continue
        info = extract_code_info(py_file)
        if info:
            cid = f"{info.get('set_name', '?')}-{info.get('number', '?')}"
            code_cards[cid] = info

    print(f"对比 {len(code_cards)} 代码 vs {len(cache)} 缓存...")
    results, passed, not_found = [], 0, 0
    for cid, ci in sorted(code_cards.items()):
        ce = cache.get(cid)
        if ce is None:
            not_found += 1
            continue
        r = compare_card(ci, ce)
        results.append(r)
        if r["passes"]:
            passed += 1

    total = len(results)
    issues_total = sum(r["issue_count"] for r in results)
    critical_total = sum(r.get("critical_count", 0) for r in results)
    warning_total = sum(r.get("warning_count", 0) for r in results)
    info_total = sum(r.get("info_count", 0) for r in results)
    report = {
        "verify_date": "2026-06-09",
        "summary": {
            "compared": total, "passed": passed, "with_issues": total - passed,
            "total_issues": issues_total,
            "critical": critical_total, "warning": warning_total, "info": info_total,
            "not_found_in_cache": not_found,
            "pass_rate": f"{passed / max(total, 1) * 100:.1f}%",
        },
        "results": results,
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    s = report["summary"]
    print(f"\n对比: {s['compared']} | 通过: {s['passed']} | 问题: {s['with_issues']}")
    print(f"问题总数: {s['total_issues']} (CRITICAL: {s['critical']}, WARNING: {s['warning']}, INFO: {s['info']})")
    print(f"通过率: {s['pass_rate']}")

    print("\n=== CRITICAL 问题 (Top 15) ===")
    critical_results = sorted(
        [r for r in results if r.get("critical_count", 0) > 0],
        key=lambda r: r["critical_count"], reverse=True
    )[:15]
    for r in critical_results:
        print(f"\n{r['card_id']} {r['name']} ({r.get('critical_count',0)} critical, {r.get('warning_count',0)} warn, {r.get('info_count',0)} info):")
        for issue in r["issues"]:
            if isinstance(issue, dict) and issue.get("severity") == "CRITICAL":
                print(f"  - ⚠️ {issue['msg']}")
            elif isinstance(issue, dict):
                print(f"  - {issue['msg']}")
            else:
                print(f"  - {issue}")

    print("\n=== 问题最多的卡牌 (Top 15) ===")
    bad = sorted([r for r in results if not r["passes"]], key=lambda r: r["issue_count"], reverse=True)[:15]
    for r in bad:
        print(f"\n{r['card_id']} {r['name']}:")
        for issue in r["issues"]:
            if isinstance(issue, dict):
                print(f"  - [{issue['severity']}] {issue['msg']}")
            else:
                print(f"  - {issue}")


if __name__ == "__main__":
    main()
