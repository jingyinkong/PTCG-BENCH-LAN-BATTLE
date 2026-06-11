#!/usr/bin/env python3
"""卡牌实现 AST 静态检查。分支级 yield + 空实现 + 条件攻击 + 四档 SuperType 规则。"""
import ast
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).parent.parent
CARDS_DIR = PROJECT_ROOT / "ptcg" / "cards"


def _supertype(src: str) -> str:
    for st, kw in [("Pokemon","PokemonCard"),("Item","ItemCard"),("Supporter","SupporterCard"),
                    ("Tool","ToolCard"),("Stadium","StadiumCard"),("Energy","EnergyCard")]:
        if kw in src: return st
    return "Unknown"


def _branch_has_yield(body_stmts: list) -> bool:
    """检查语句列表中是否有 yield."""
    for s in body_stmts:
        if isinstance(s, (ast.Yield, ast.YieldFrom)):
            return True
        for child in ast.walk(s):
            if isinstance(child, (ast.Yield, ast.YieldFrom)):
                return True
    return False


def _branch_is_empty(body_stmts: list) -> bool:
    """检查分支是否只有简单赋值（空实现）."""
    for s in body_stmts:
        if isinstance(s, (ast.Yield, ast.YieldFrom, ast.Expr)):
            continue
        if isinstance(s, ast.Assign):
            continue
        if isinstance(s, ast.If):
            continue
        return False
    # 所有语句都是赋值或 yield → 检查是否有 yield
    has_yield = _branch_has_yield(body_stmts)
    # 只有赋值 → 空实现
    has_real_call = any(
        isinstance(s, ast.Expr) and isinstance(s.value, ast.Call)
        for s in body_stmts
    )
    return not has_yield and not has_real_call and len(body_stmts) >= 1


def _find_action_branches(tree: ast.AST, source: str) -> Dict[str, dict]:
    """找到 reduce_action 中每个 action 类型的处理分支。返回 {action_type: {has_yield, is_empty, body}}."""
    branches = {}
    action_types = ["UseAbilityAction", "AttackAction", "UseItemAction",
                    "UseSupporterAction", "PlayPokemonAction", "EvolvePokemonAction",
                    "RetreatAction", "UseToolAction"]

    for node in ast.walk(tree):
        if not (isinstance(node, ast.FunctionDef) and node.name == "reduce_action"):
            continue
        # 遍历所有 if/elif 分支
        for stmt in node.body:
            if isinstance(stmt, ast.If):
                _extract_if_chain(stmt, branches, action_types)
    return branches


def _extract_if_chain(if_node: ast.If, branches: dict, action_types: list):
    """递归提取 if/elif/else 链中的所有 isinstance 分支."""
    if isinstance(if_node.test, ast.Call):
        test_str = ast.unparse(if_node.test) if hasattr(ast, "unparse") else ""
        if "isinstance" in test_str:
            for at in action_types:
                if at in test_str:
                    branches[at] = {
                        "has_yield": _branch_has_yield(if_node.body),
                        "is_empty": _branch_is_empty(if_node.body),
                        "body": if_node.body
                    }
    # 处理 elif（orelse 中的 If）
    for stmt in if_node.orelse:
        if isinstance(stmt, ast.If):
            _extract_if_chain(stmt, branches, action_types)


def validate_card(filepath: Path) -> List[str]:
    """验证单张卡牌，返回违规列表."""
    violations = []
    source = filepath.read_text(encoding="utf-8")
    st = _supertype(source)

    if "def reduce_action" not in source:
        return violations

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return [f"语法错误: {filepath.name}"]

    branches = _find_action_branches(tree, source)

    # === Pokemon 规则 ===
    if st == "Pokemon":
        # 1. UseAbilityAction 分支必须有 yield
        if "UseAbilityAction" in branches:
            ab = branches["UseAbilityAction"]
            if not ab["has_yield"]:
                violations.append(
                    f"[Pokemon] UseAbilityAction 分支缺少 yield: {filepath.name}"
                )
            if ab["is_empty"]:
                violations.append(
                    f"[Pokemon] UseAbilityAction 分支空实现（只有标记位赋值）: {filepath.name}"
                )

        # 2. AttackAction 条件检查
        if "AttackAction" in branches:
            atk = branches["AttackAction"]
            # 检查攻击文本是否有条件
            cond_kws = ["如果", "若", "否则", "失败", "fails", "does nothing"]
            has_cond_text = any(kw in source for kw in cond_kws)
            if has_cond_text:
                # 检查 AttackAction 分支是否有额外 if 判断
                has_if_check = any(isinstance(s, ast.If) for s in atk["body"])
                if not has_if_check:
                    violations.append(
                        f"[Pokemon] 攻击文本有条件但 AttackAction 分支未检查: {filepath.name}"
                    )

    # === Item/Supporter 规则 ===
    elif st in ("Item", "Supporter"):
        has_use_action = "UseItemAction" in source or "UseSupporterAction" in source
        if has_use_action:
            any_yield = any(b["has_yield"] for b in branches.values())
            if not any_yield:
                violations.append(
                    f"[{st}] get_actions 返回 UseAction 但 reduce_action 缺少 yield: {filepath.name}"
                )

    return violations


def validate_all(verbose: bool = False, card_id: Optional[str] = None):
    violations = []
    stats = {"total": 0}
    for st_name in ["Pokemon", "Item", "Supporter", "Tool", "Stadium", "Energy"]:
        stats[st_name] = 0

    for py_file in sorted(CARDS_DIR.rglob("*.py")):
        if py_file.name == "__init__.py":
            continue
        if card_id:
            cid_lower = card_id.lower().replace("-", "")
            if cid_lower not in py_file.name.lower():
                continue
        stats["total"] += 1
        source = py_file.read_text(encoding="utf-8")
        st = _supertype(source)
        if st in stats:
            stats[st] += 1

        for v in validate_card(py_file):
            violations.append({"file": str(py_file.relative_to(CARDS_DIR)),
                               "supertype": st, "violation": v})
            if verbose:
                print(f"  {v}")

    return violations, stats


def main():
    import argparse
    p = argparse.ArgumentParser(description="卡牌 AST 静态检查")
    p.add_argument("--verbose", "-v", action="store_true")
    p.add_argument("--card-id")
    args = p.parse_args()
    violations, stats = validate_all(verbose=args.verbose, card_id=args.card_id)
    print(f"\n=== AST 静态检查报告 ===")
    print(f"总卡牌: {stats['total']}  |  Pokemon: {stats['Pokemon']}  Item: {stats['Item']}"
          f"  Supporter: {stats['Supporter']}  Tool: {stats['Tool']}"
          f"  Stadium: {stats['Stadium']}  Energy: {stats['Energy']}")
    print(f"违规: {len(violations)}")
    by_type: Dict[str, List[str]] = {}
    for v in violations:
        by_type.setdefault(v["supertype"], []).append(v["violation"])
    for st, items in sorted(by_type.items()):
        print(f"\n  [{st}] {len(items)} 违规:")
        for item in items[:12]:
            print(f"    {item}")
        if len(items) > 12:
            print(f"    ... 及其他 {len(items) - 12} 项")
    if violations:
        print(f"\n结论: {len(violations)} 违规。需要修复。")
        return 1
    else:
        print(f"\n结论: 0 违规。全部检查通过！")
        return 0


if __name__ == "__main__":
    sys.exit(main())
