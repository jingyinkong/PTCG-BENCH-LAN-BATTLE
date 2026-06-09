"""PTCG 卡牌结构完整性扫描脚本 (L1-L3).

L1: __init__ 中 ability/attacks 定义完整性
L2: get_actions() 中 Action 生成覆盖率
L3: reduce_action() 中 isinstance 分支覆盖率

用法: uv run python scripts/scan_cards.py
输出: .omc/state/card-scan-report.json
"""
import ast
import json
import re
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).parent.parent
CARDS_DIR = PROJECT_ROOT / "ptcg" / "cards"
OUTPUT_PATH = PROJECT_ROOT / ".omc" / "state" / "card-scan-report.json"


ACTION_CLASSES = {
    "AttackAction": "attack",
    "UseAbilityAction": "ability",
    "UseItemAction": "item_effect",
    "UseSupporterAction": "supporter_effect",
    "UseStadiumAction": "stadium_effect",
    "EvolvePokemonAction": "evolution",
    "RetreatAction": "retreat",
    "PlayPokemonAction": "play",
}


def parse_card_file(filepath: Path) -> dict[str, Any] | None:
    """Parse a single card file and return L1-L3 analysis."""
    try:
        with open(filepath, encoding="utf-8") as f:
            source = f.read()
    except Exception as e:
        return {"file": str(filepath), "error": str(e)}

    tree = ast.parse(source)
    rel_path = filepath.relative_to(CARDS_DIR)

    card_class = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for base in node.bases:
                base_name = base.id if isinstance(base, ast.Name) else (
                    base.attr if isinstance(base, ast.Attribute) else ""
                )
                if base_name in (
                    "PokemonCard", "EnergyCard", "SpecialEnergyCard",
                    "ItemCard", "SupporterCard", "StadiumCard", "ToolCard",
                ):
                    card_class = node
                    break
            if card_class:
                break

    if card_class is None:
        return {
            "file": str(rel_path),
            "error": "No Card subclass found",
            "card_type": "unknown",
        }

    card_type = _get_card_type(card_class)
    init_node = _find_method(card_class, "__init__")
    get_actions_node = _find_method(card_class, "get_actions")
    reduce_action_node = _find_method(card_class, "reduce_action")

    card_name = card_class.name

    result = {
        "file": str(rel_path),
        "class": card_name,
        "card_type": card_type,
        "has_get_actions": get_actions_node is not None,
        "has_reduce_action": reduce_action_node is not None,
    }

    l1 = _check_l1(source, init_node, card_type)
    result["l1_structure"] = l1

    class_source = _get_node_source(source, card_class)
    l2 = _check_l2(source, class_source, get_actions_node, card_type, l1)
    result["l2_actions"] = l2

    l3 = _check_l3(source, reduce_action_node, l2)  # source = full file, for correct line numbers
    result["l3_handler"] = l3

    issues = []
    if l1.get("issues"):
        issues.extend(l1["issues"])
    if l2.get("issues"):
        issues.extend(l2["issues"])
    if l3.get("issues"):
        issues.extend(l3["issues"])

    result["issues"] = issues
    result["passes"] = len(issues) == 0
    result["issue_count"] = len(issues)

    return result


def _get_card_type(class_node: ast.ClassDef) -> str:
    for base in class_node.bases:
        if isinstance(base, ast.Name):
            return base.id
        elif isinstance(base, ast.Attribute):
            return base.attr
    return "unknown"


def _find_method(class_node: ast.ClassDef, method_name: str) -> ast.FunctionDef | None:
    for node in ast.iter_child_nodes(class_node):
        if isinstance(node, ast.FunctionDef) and node.name == method_name:
            return node
    return None


def _get_node_source(source: str, node: ast.AST) -> str:
    if hasattr(node, "lineno") and hasattr(node, "end_lineno"):
        lines = source.split("\n")
        return "\n".join(lines[node.lineno - 1: node.end_lineno])
    return ""


def _check_l1(source: str, init_node: ast.FunctionDef | None, card_type: str) -> dict[str, Any]:
    result = {
        "has_ability_def": False,
        "has_active_ability": False,
        "has_passive_ability": False,
        "has_attacks_def": False,
        "has_energy_def": False,
        "has_attachment_def": False,
        "issues": [],
        "passes": True,
    }

    if init_node is None:
        result["issues"].append("L1: 缺少 __init__ 方法")
        result["passes"] = False
        return result

    init_source = _get_node_source(source, init_node)

    if re.search(r"self\.ability\s*=", init_source):
        result["has_ability_def"] = True
        if "ActiveAbility" in init_source:
            result["has_active_ability"] = True
        if "PassiveAbility" in init_source:
            result["has_passive_ability"] = True
    if re.search(r"self\.attacks\s*=", init_source):
        result["has_attacks_def"] = True
    if re.search(r"self\.energy\s*=", init_source):
        result["has_energy_def"] = True
    if re.search(r"self\.attachment\s*=", init_source):
        result["has_attachment_def"] = True

    if card_type == "PokemonCard" and not result["has_attacks_def"]:
        result["issues"].append("L1: PokemonCard 缺少 self.attacks 定义")
        result["passes"] = False

    return result


def _check_l2(
    source: str,
    class_source: str,
    get_actions_node: ast.FunctionDef | None,
    card_type: str,
    l1: dict[str, Any],
) -> dict[str, Any]:
    result = {
        "generated_actions": [],
        "missing_actions": [],
        "issues": [],
        "passes": True,
    }

    # Check get_actions() using full-file source (not class_source)
    # because AST node line numbers reference the full file
    if get_actions_node is not None:
        ga_source = _get_node_source(source, get_actions_node)
        for action_class in ACTION_CLASSES:
            if action_class in ga_source:
                result["generated_actions"].append(action_class)

    # Active abilities need UseAbilityAction - check full class for helper methods
    if l1.get("has_active_ability") and "UseAbilityAction" not in result["generated_actions"]:
        if "UseAbilityAction" in class_source:
            result["generated_actions"].append("UseAbilityAction")
        else:
            result["missing_actions"].append("UseAbilityAction")
            result["issues"].append("L2: ActiveAbility 定义了但未使用 UseAbilityAction")
            result["passes"] = False

    if l1.get("has_attacks_def") and "AttackAction" not in result["generated_actions"]:
        result["missing_actions"].append("AttackAction")
        result["issues"].append("L2: 定义了 attacks 但 get_actions() 未生成 AttackAction")
        result["passes"] = False

    if card_type == "ItemCard" and "UseItemAction" not in result["generated_actions"]:
        result["missing_actions"].append("UseItemAction")
        result["issues"].append("L2: ItemCard 未生成 UseItemAction")
        result["passes"] = False

    if card_type == "SupporterCard" and "UseSupporterAction" not in result["generated_actions"]:
        result["missing_actions"].append("UseSupporterAction")
        result["issues"].append("L2: SupporterCard 未生成 UseSupporterAction")
        result["passes"] = False

    return result


def _check_l3(
    source: str,
    reduce_action_node: ast.FunctionDef | None,
    l2: dict[str, Any],
) -> dict[str, Any]:
    result = {
        "handled_actions": [],
        "unhandled_actions": [],
        "issues": [],
        "passes": True,
    }

    if reduce_action_node is None:
        result["issues"].append("L3: 缺少 reduce_action() 方法")
        result["passes"] = False
        return result

    ra_source = _get_node_source(source, reduce_action_node)

    for action_class in ACTION_CLASSES:
        if f"isinstance(action, {action_class})" in ra_source:
            result["handled_actions"].append(action_class)

    for action in l2.get("generated_actions", []):
        if action not in result["handled_actions"]:
            result["unhandled_actions"].append(action)
            result["issues"].append(
                f"L3: get_actions() 生成 {action} 但 reduce_action() 未处理"
            )
            result["passes"] = False

    return result


def scan_all_cards() -> dict[str, Any]:
    all_results = []
    total = 0
    passed = 0
    failed = 0
    errors = 0
    card_types_found: dict[str, int] = {}
    issue_summary: dict[str, list[str]] = {}

    for py_file in sorted(CARDS_DIR.rglob("*.py")):
        if py_file.name == "__init__.py":
            continue
        total += 1
        result = parse_card_file(py_file)
        if result is None:
            continue

        if "error" in result and result.get("card_type") == "unknown":
            errors += 1
        else:
            ct = result.get("card_type", "unknown")
            card_types_found[ct] = card_types_found.get(ct, 0) + 1

            if result.get("passes"):
                passed += 1
            else:
                failed += 1
                for issue in result.get("issues", []):
                    issue_type = issue.split(":")[0] if ":" in issue else "other"
                    if issue_type not in issue_summary:
                        issue_summary[issue_type] = []
                    issue_summary[issue_type].append(str(result["file"]))

        all_results.append(result)

    report = {
        "scan_date": "2026-06-09",
        "summary": {
            "total_cards": total,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "pass_rate": f"{passed / max(total, 1) * 100:.1f}%",
            "card_types": card_types_found,
        },
        "issue_summary": {
            k: {"count": len(v), "files": v[:10]}
            for k, v in issue_summary.items()
        },
        "failed_cards": [
            {
                "file": r["file"],
                "class": r.get("class", "unknown"),
                "card_type": r.get("card_type", "unknown"),
                "issue_count": r.get("issue_count", 0),
                "issues": r.get("issues", []),
            }
            for r in all_results if not r.get("passes") and "error" not in r
        ],
        "error_cards": [
            {"file": r["file"], "error": r["error"]}
            for r in all_results if "error" in r
        ],
        "all_results": all_results,
    }

    return report


def main():
    print(f"扫描卡牌目录: {CARDS_DIR}")
    print(f"输出报告: {OUTPUT_PATH}\n")

    report = scan_all_cards()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    s = report["summary"]
    print(f"卡牌总数: {s['total_cards']}")
    print(f"通过: {s['passed']} | 失败: {s['failed']} | 错误: {s['errors']}")
    print(f"通过率: {s['pass_rate']}")
    print()
    print("按卡牌类型分布:")
    for ct, count in sorted(s["card_types"].items()):
        print(f"  {ct}: {count}")
    print()
    print("问题汇总:")
    for issue_type, info in sorted(report["issue_summary"].items()):
        print(f"  {issue_type}: {info['count']} 张卡")
        if info["count"] <= 5:
            for f in info["files"]:
                print(f"    - {f}")
    print()
    print(f"详细报告已写入 {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
