"""AST 深度分析器 — 对 CUSTOM 类型卡牌进行 reduce_action 源码解析。

用法:
  uv run python scripts/ast_effect_analyzer.py --card CARD_ID   # 单卡分析
  uv run python scripts/ast_effect_analyzer.py --all             # 所有 CUSTOM 卡
  uv run python scripts/ast_effect_analyzer.py --report          # 汇总报告
"""
import ast
import json
import argparse
from pathlib import Path
from enum import Enum, auto

PROJECT_ROOT = Path(__file__).parent.parent
CARDS_DIR = PROJECT_ROOT / "ptcg" / "cards"


class Confidence(Enum):
    """生成置信度."""
    HIGH = auto()    # 模板直接适用
    MEDIUM = auto()  # AST 分析推导
    LOW = auto()     # 需人工标记


class ASTEffectAnalyzer:
    """解析卡牌 reduce_action 方法 AST，提取效果模式."""

    def __init__(self, source: str):
        self.source = source
        self.tree = None
        self._findings: dict = {}
        try:
            self.tree = ast.parse(source)
        except SyntaxError:
            pass

    def analyze(self) -> dict:
        """分析 reduce_action 方法并返回结果."""
        if not self.tree:
            return self._empty_result()

        reduce_node = None
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef) and node.name == "reduce_action":
                reduce_node = node
                break

        if not reduce_node:
            return self._empty_result()

        findings = {
            "yields": self._find_yields(reduce_node),
            "assignments": self._find_assignments(reduce_node),
            "calls": self._find_calls(reduce_node),
            "branches": self._find_branches(reduce_node),
        }
        self._findings = findings
        return findings

    def _find_yields(self, node) -> list[str]:
        yields = []
        for n in ast.walk(node):
            if isinstance(n, (ast.Yield, ast.YieldFrom)):
                parent = getattr(n, "_parent", None)
                yields.append(ast.unparse(parent)[:100] if parent else "yield")
        return yields

    def _find_assignments(self, node) -> list[str]:
        assigns = set()
        for n in ast.walk(node):
            if isinstance(n, ast.Assign):
                for target in n.targets:
                    if isinstance(target, ast.Attribute):
                        obj_name = ""
                        val = target.value
                        if isinstance(val, ast.Name):
                            obj_name = val.id
                        elif isinstance(val, ast.Attribute):
                            obj_name = self._resolve_attr(val)
                        assigns.add(f"{obj_name}.{target.attr}" if obj_name else target.attr)
        return sorted(assigns)

    def _find_calls(self, node) -> list[str]:
        calls = set()
        skip = {"isinstance", "print", "len", "str", "int", "range", "enumerate", "list"}
        for n in ast.walk(node):
            if isinstance(n, ast.Call):
                name = self._resolve_call(n)
                if name and name not in skip:
                    calls.add(name)
        return sorted(calls)

    def _find_branches(self, node) -> list[str]:
        branches = []
        for n in ast.walk(node):
            if isinstance(n, ast.If):
                cond = ast.unparse(n.test)[:80]
                branches.append(cond)
        return branches

    def _resolve_attr(self, node) -> str:
        if isinstance(node, ast.Attribute):
            inner = self._resolve_attr(node.value) if isinstance(node.value, ast.Attribute) else (
                node.value.id if isinstance(node.value, ast.Name) else "?")
            return f"{inner}.{node.attr}"
        return str(node)

    def _resolve_call(self, node) -> str:
        func = node.func
        if isinstance(func, ast.Name):
            return func.id
        if isinstance(func, ast.Attribute):
            inner = func.value.id if isinstance(func.value, ast.Name) else (
                self._resolve_attr(func.value) if isinstance(func.value, ast.Attribute) else "?")
            return f"{inner}.{func.attr}"
        return ""

    def _empty_result(self) -> dict:
        return {"yields": [], "assignments": [], "calls": [], "branches": []}

    def classify_confidence(self) -> Confidence:
        """根据分析结果评估置信度."""
        f = self._findings
        n_yields = len(f.get("yields", []))
        n_assigns = len(f.get("assignments", []))
        n_calls = len(f.get("calls", []))
        n_branches = len(f.get("branches", []))

        if n_yields == 0 and n_assigns <= 2 and n_calls <= 3:
            return Confidence.HIGH
        if n_yields <= 2 and n_calls <= 5:
            return Confidence.MEDIUM
        return Confidence.LOW


def _find_card_source(card_id: str) -> tuple[str, str]:
    set_code, num = card_id.split("-") if "-" in card_id else ("???", "???")
    pattern = f"{set_code.lower()}{num.lower()}"
    num_nozero = num.lstrip("0") or "0"
    pattern_short = f"{set_code.lower()}{num_nozero.lower()}"
    for py_file in CARDS_DIR.rglob("*.py"):
        fname = py_file.name
        if fname.startswith(pattern) or fname.startswith(pattern_short):
            if fname.endswith(".py") and "__pycache__" not in str(py_file):
                return py_file.read_text(encoding="utf-8"), str(py_file)
    return "", ""


def analyze_card(card_id: str) -> dict | None:
    source, filepath = _find_card_source(card_id)
    if not source:
        return None
    analyzer = ASTEffectAnalyzer(source)
    findings = analyzer.analyze()
    confidence = analyzer.classify_confidence()
    return {
        "card_id": card_id, "file": filepath,
        "findings": findings, "confidence": confidence.name,
    }


def analyze_custom_cards() -> list[dict]:
    from test_templates import classify_card, EffectType
    cache_path = PROJECT_ROOT / "card_data_cache.json"
    if not cache_path.exists():
        return []
    cache = json.loads(cache_path.read_text(encoding="utf-8"))
    results = []
    for cid in sorted(cache.keys()):
        effect, reason = classify_card(cid)
        if effect == EffectType.CUSTOM and "未找到" not in reason:
            name = cache[cid].get("name", "Unknown")
            analysis = analyze_card(cid)
            if analysis:
                analysis["name"] = name
                analysis["effect_reason"] = reason
                results.append(analysis)
                print(f"  {cid} {name}: confidence={analysis['confidence']}")
    return results


def print_report(results: list[dict]):
    counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for r in results:
        counts[r["confidence"]] = counts.get(r["confidence"], 0) + 1
    print(f"\n{'='*60}")
    print(f"  AST 深度分析报告 — {len(results)} 张 CUSTOM 卡牌")
    print(f"{'='*60}")
    for level in ["HIGH", "MEDIUM", "LOW"]:
        n = counts.get(level, 0)
        bar = "█" * n
        print(f"  {level:<10s} {n:>3d} 张  {bar}")
    print(f"{'='*60}")

    for r in results:
        f = r["findings"]
        print(f"\n  [{r['confidence']}] {r['card_id']} {r['name']}")
        print(f"    {r['effect_reason']}")
        print(f"    Yields: {len(f['yields'])} | Assignments: {len(f['assignments'])} "
              f"| Calls: {len(f['calls'])} | Branches: {len(f['branches'])}")
        if f["yields"]:
            print(f"    Interaction: {f['yields'][:3]}")
        if f["calls"]:
            print(f"    Calls: {f['calls'][:5]}")
        if f["branches"]:
            print(f"    Branches: {f['branches'][:3]}")


def main():
    p = argparse.ArgumentParser(description="卡牌 AST 深度效果分析")
    p.add_argument("--card", metavar="CARD_ID", help="分析指定卡牌")
    p.add_argument("--all", action="store_true", help="分析所有 CUSTOM 卡牌")
    p.add_argument("--report", action="store_true", help="仅输出汇总报告")
    args = p.parse_args()

    if args.card:
        result = analyze_card(args.card)
        if result:
            print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
        else:
            print(f"未找到卡牌: {args.card}")

    if args.all or args.report:
        results = analyze_custom_cards()
        print_report(results)


if __name__ == "__main__":
    main()
