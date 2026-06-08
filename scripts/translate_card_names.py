#!/usr/bin/env python3
"""
使用 card_chinese_data.json 更新卡片 Python 代码，将英文名称改为中文。
用法: uv run python scripts/translate_card_names.py [--dry-run] [--card "Card Name"]
"""
import argparse
import ast
import json
import sys
from pathlib import Path

CARDS_DIR = Path(__file__).parent.parent / "ptcg" / "cards"
DATA_FILE = Path(__file__).parent.parent / "card_chinese_data.json"


def load_chinese_data() -> dict:
    if not DATA_FILE.exists():
        print(f"[ERROR] 数据文件不存在: {DATA_FILE}")
        print("请先运行: uv run python scripts/fetch_chinese_card_data.py")
        sys.exit(1)
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def translate_file(file_path: Path, card_data: dict, dry_run: bool = False) -> bool:
    try:
        source = file_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"  [ERROR] 读取失败: {e}")
        return False

    en_name = card_data["english_name"]
    cn_name = card_data["chinese_name"]
    attacks_en = card_data.get("attacks_en", [])
    attacks_cn = card_data.get("attacks_cn", [])
    abilities_en = card_data.get("abilities_en", [])
    abilities_cn = card_data.get("abilities_cn", [])

    modified = source
    changes = []

    # 卡片主名称
    old = f'self.name = "{en_name}"'
    new = f'self.name = "{cn_name}"'
    if old in modified:
        modified = modified.replace(old, new)
        changes.append(f"卡片名: {en_name} → {cn_name}")
    else:
        print(f"  [WARN] 未找到卡片名: {old}")

    # 攻击名
    for en_atk, cn_atk in zip(attacks_en, attacks_cn):
        old_a = f'"name": "{en_atk}"'
        new_a = f'"name": "{cn_atk}"'
        if old_a in modified:
            modified = modified.replace(old_a, new_a)
            changes.append(f"招式: {en_atk} → {cn_atk}")
        else:
            print(f"  [WARN] 未找到招式名: {en_atk}")

    # 特性名
    for en_abi, cn_abi in zip(abilities_en, abilities_cn):
        old_a = f'"name": "{en_abi}"'
        new_a = f'"name": "{cn_abi}"'
        if old_a in modified:
            modified = modified.replace(old_a, new_a)
            changes.append(f"特性: {en_abi} → {cn_abi}")
        else:
            print(f"  [WARN] 未找到特性名: {en_abi}")

    if modified == source:
        return False

    if dry_run:
        print(f"  [DRY-RUN] 将做 {len(changes)} 处修改:")
        for c in changes:
            print(f"    - {c}")
        return False

    file_path.write_text(modified, encoding="utf-8")
    for c in changes:
        print(f"    ✓ {c}")
    return True


def main():
    parser = argparse.ArgumentParser(description="翻译卡片代码中的英文名称为中文")
    parser.add_argument("--dry-run", action="store_true", help="只预览，不实际修改")
    parser.add_argument("--card", type=str, default="", help="只翻译指定卡片（英文名）")
    parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")
    args = parser.parse_args()

    data = load_chinese_data()
    cards = data.get("cards", {})
    not_found = data.get("not_found", [])

    print("=" * 60)
    print("PTCG 卡片名称中文化")
    print(f"数据源: {DATA_FILE}")
    print(f"可用: {len(cards)} 张 | 未找到: {len(not_found)} 张")
    if args.dry_run:
        print("模式: DRY-RUN（不实际修改）")
    print("=" * 60)

    total = 0
    modified = 0
    skipped = 0

    for py_file in sorted(CARDS_DIR.rglob("*.py")):
        if py_file.name.startswith("__"):
            continue

        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except SyntaxError:
            continue

        en_name = None
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if (isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name)
                        and target.value.id == "self" and target.attr == "name"
                        and isinstance(node.value, ast.Constant)):
                        en_name = node.value.value
                        break
                if en_name:
                    break

        if en_name is None:
            continue

        total += 1

        if args.card and en_name != args.card:
            continue

        if en_name not in cards:
            if en_name in not_found:
                if args.verbose:
                    print(f"\n  [{total}] {py_file.stem}: {en_name} — 未找到翻译，跳过")
            else:
                print(f"\n  [{total}] {py_file.stem}: {en_name} — 无数据")
            skipped += 1
            continue

        card_data = cards[en_name]
        cn_name = card_data.get("chinese_name", "")

        if en_name == cn_name:
            if args.verbose:
                print(f"\n  [{total}] {py_file.stem}: {en_name} — 已是中文，跳过")
            skipped += 1
            continue

        print(f"\n  [{total}] {py_file.stem}: {en_name} → {cn_name}")
        if translate_file(py_file, card_data, dry_run=args.dry_run):
            modified += 1

    print(f"\n{'=' * 60}")
    print(f"总计: {total} | 修改: {modified} | 跳过: {skipped}")
    if args.dry_run:
        print("DRY-RUN — 未实际修改。去掉 --dry-run 执行。")
    print("完成!")


if __name__ == "__main__":
    main()
