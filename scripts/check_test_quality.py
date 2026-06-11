"""测试质量扫描器 — skeleton attestions, snapshot_game 使用率, 平均断言数。

用法:
  uv run python scripts/check_test_quality.py
  uv run python scripts/check_test_quality.py --dir tests/cards/generated/
"""
import argparse
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


def analyze_file(filepath: Path) -> dict:
    """分析单个测试文件的质量指标."""
    if not filepath.suffix == ".py":
        return {}
    content = filepath.read_text(encoding="utf-8")
    lines = content.split("\n")

    skeleton_count = len(re.findall(r"assert\s+\w+\s+is\s+not\s+None", content))
    skeleton_lines = [
        i + 1 for i, line in enumerate(lines)
        if re.search(r"assert\s+\w+\s+is\s+not\s+None", line)
    ]
    uses_snapshot = "snapshot_game" in content
    assert_patterns = re.findall(r"^\s*assert\s+", content, re.MULTILINE)
    total_asserts = len(assert_patterns)
    test_count = len(re.findall(r"^\s*def test_", content, re.MULTILINE))
    avg_asserts = total_asserts / test_count if test_count else 0

    return {
        "file": str(filepath.relative_to(PROJECT_ROOT)),
        "test_count": test_count,
        "total_asserts": total_asserts,
        "skeleton_count": skeleton_count,
        "skeleton_lines": skeleton_lines,
        "avg_asserts": round(avg_asserts, 1),
        "uses_snapshot": uses_snapshot,
        "passes": skeleton_count == 0 and avg_asserts >= 2,
    }


def scan_directory(directory: str) -> list[dict]:
    results = []
    root = Path(directory) if Path(directory).is_absolute() else PROJECT_ROOT / directory
    for py_file in sorted(root.rglob("test_*.py")):
        result = analyze_file(py_file)
        if result:
            results.append(result)
    return results


def print_report(results: list[dict], verbose: bool = False):
    total = len(results)
    passing = sum(1 for r in results if r["passes"])
    total_skeletons = sum(r["skeleton_count"] for r in results)
    snapshot_users = sum(1 for r in results if r["uses_snapshot"])
    avg_all = sum(r["avg_asserts"] for r in results) / total if total else 0

    print(f"\n{'='*60}")
    print(f"  测试质量扫描报告 — {total} 文件")
    print(f"{'='*60}")
    print(f"  质量通过: {passing}/{total} ({passing/total*100:.1f}%)" if total else "")
    print(f"  Skeleton 断言残留: {total_skeletons} 处")
    print(f"  snapshot_game 使用: {snapshot_users}/{total}" if total else "")
    print(f"  平均断言数/方法: {avg_all:.1f}")
    print(f"{'='*60}")

    problem_files = [r for r in results if r["skeleton_count"] > 0]
    if problem_files:
        print(f"\n  ⚠ skeleton 断言残留 ({len(problem_files)} 文件):")
        for r in sorted(problem_files, key=lambda x: -x["skeleton_count"])[:15]:
            print(f"    {r['skeleton_count']:>3d}  {r['file']}")

    low = [r for r in results if r["avg_asserts"] < 2 and r["test_count"] > 0]
    if low:
        print(f"\n  ⚠ 低断言密度 ({len(low)} 文件, <2/test):")
        for r in sorted(low, key=lambda x: x["avg_asserts"])[:10]:
            print(f"    avg={r['avg_asserts']}  {r['file']}")

    if total_skeletons == 0:
        print(f"\n  ✅ 零 skeleton 断言残留")
    else:
        print(f"\n  ❌ {total_skeletons} 处 skeleton 断言需修复")


def main():
    p = argparse.ArgumentParser(description="测试质量扫描器")
    p.add_argument("--dir", default="tests/cards/generated", help="扫描目录")
    p.add_argument("--verbose", "-v", action="store_true")
    args = p.parse_args()
    results = scan_directory(args.dir)
    print_report(results, verbose=args.verbose)


if __name__ == "__main__":
    main()
