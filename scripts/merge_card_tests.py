#!/usr/bin/env python3
"""合并 PTCG 卡牌测试文件 — 每卡合并为 1 个 test_{set}_{num}.py。

用法:
    python scripts/merge_card_tests.py --dry-run          # 预览模式
    python scripts/merge_card_tests.py --set ASR           # 只处理单个 set
    python scripts/merge_card_tests.py --all               # 处理全部 38 个 set
"""

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Set

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent
GENERATED_DIR = PROJECT_ROOT / "tests" / "cards" / "generated"
CARDS_SRC_DIR = PROJECT_ROOT / "ptcg" / "cards"

# 所有有目录的 set
SET_DIRS = sorted(
    d.name
    for d in GENERATED_DIR.iterdir()
    if d.is_dir() and not d.name.startswith("_")
)


# ─── 辅助函数 ────────────────────────────────────────────────────────

def _extract_card_id_from_file(path: Path) -> Optional[str]:
    """从文件内容提取 CARD_ID = "XXX-XXX" 变量。"""
    try:
        content = path.read_text(encoding="utf-8")
        m = re.search(r'CARD_ID\s*=\s*"([^"]+)"', content)
        if m:
            return m.group(1)
        # 有些文件直接写 registry.get("XXX-XXX")
        m = re.search(r'registry\.get\s*\(\s*"([^"]+)"\s*\)', content)
        if m:
            return m.group(1)
    except Exception:
        pass
    return None


def _card_id_from_filename(filename: str) -> Optional[str]:
    """从文件名 test_SET_NUM_xxx.py 提取 SET_NUM → SET-NUM。"""
    m = re.match(r"test_([a-z]+)_(\d+)(_|$)", filename)
    if m:
        set_code = m.group(1).upper()
        return f"{set_code}-{m.group(2)}"
    return None


def _group_test_files(set_code: str) -> Dict[str, Dict[str, List[Path]]]:
    """将单个 set 目录下所有测试文件按 CARD_ID 分组。

    返回: { card_id: {"l3": [...], "behavior": [...], "snapshot": [...], "nolabel": [...]} }
    """
    set_dir = GENERATED_DIR / set_code
    if not set_dir.is_dir():
        return {}

    by_card: Dict[str, Dict[str, List[Path]]] = defaultdict(
        lambda: {"l3": [], "behavior": [], "snapshot": [], "nolabel": []}
    )

    for f in sorted(set_dir.iterdir()):
        if not f.name.endswith(".py") or f.name.startswith("__"):
            continue

        # 尝试从文件名提取 card_id
        card_id = _card_id_from_filename(f.name)

        # 如果文件名不包含标准标识符（中文名-only），从内容提取
        if card_id is None:
            card_id = _extract_card_id_from_file(f)

        if card_id is None:
            print(f"  [WARN] 无法识别 card_id: {f.name}")
            continue

        # 根据后缀分类
        name = f.name
        if "_behavior" in name:
            by_card[card_id]["behavior"].append(f)
        elif "_snapshot" in name:
            by_card[card_id]["snapshot"].append(f)
        else:
            # l3 候选：判断是否包含实质内容（非空 L3 class）
            by_card[card_id]["l3"].append(f)

    return dict(by_card)


def _safe_get_registry():
    """安全导入并触发 registry 加载。"""
    sys.path.insert(0, str(PROJECT_ROOT))
    from ptcg.core.card_registry import registry
    registry._ensure_loaded()
    return registry


def _get_card_class(card_id: str):
    """获取卡牌类，失败返回 None。"""
    try:
        registry = _safe_get_registry()
        return registry.get(card_id)
    except Exception as e:
        print(f"  [WARN] 无法加载 card {card_id}: {e}")
        return None


def _extract_imports(content: str) -> List[str]:
    """从文件内容提取 import 语句。"""
    imports = []
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            imports.append(stripped)
    return imports


def _deduplicate_imports(all_imports: List[str]) -> List[str]:
    """收集所有 import → 按 module 合并符号 → 分类排序。

    例如 'from ptcg.core.enums import CardType' 和
    'from ptcg.core.enums import CardType, PokemonType, Stage' 会合并为一条。
    分类顺序: 标准库 → 第三方 → 项目内 ptcg.
    """
    from collections import OrderedDict

    # 按 module 分组：{ "from ptcg.core.enums": set("CardType", ...) }
    from_imports: Dict[str, Set[str]] = {}
    direct_imports: List[str] = []

    for imp in all_imports:
        imp = imp.strip()
        if imp.startswith("from ") and " import " in imp:
            parts = imp.split(" import ", 1)
            module = parts[0][5:].strip()  # 去掉 "from "
            symbols = {s.strip() for s in parts[1].split(",")}
            if module not in from_imports:
                from_imports[module] = set()
            from_imports[module].update(symbols)
        elif imp.startswith("import ") and not imp.startswith("from "):
            direct_imports.append(imp)

    # 排序后组装
    merged: List[str] = []

    # 直接 import 去重
    direct_unique = list(dict.fromkeys(direct_imports))

    # 标准库 (非 ptcg)
    for module in sorted(from_imports.keys()):
        if module.startswith("ptcg") or module.startswith("ptcg."):
            continue
        symbols = sorted(from_imports[module])
        merged.append(f"from {module} import {', '.join(symbols)}")

    # 第三方 (无前缀 ptcg)
    for imp in sorted(direct_unique):
        merged.append(imp)

    # 项目内 ptcg.
    for module in sorted(from_imports.keys()):
        if module.startswith("ptcg") or module.startswith("ptcg."):
            symbols = sorted(from_imports[module])
            merged.append(f"from {module} import {', '.join(symbols)}")

    return merged


def _generate_l3_class(card_id: str, set_code: str, num: str) -> str:
    """根据 registry 卡牌属性生成 L3 精确断言。"""
    card_cls = _get_card_class(card_id)
    if card_cls is None:
        # 如果无法加载，生成 basic 占位
        cls_name = f"Test{set_code}{num}L3Structure"
        return (
            f"class {cls_name}:\n"
            f'    """L3: 精确属性断言 - 卡牌未注册."""\n'
            "    def test_card_identity(self, card):\n"
            f'        assert card.id == "{card_id}"\n'
        )

    try:
        instance = card_cls()
    except Exception as e:
        cls_name = f"Test{set_code}{num}L3Structure"
        return (
            f"class {cls_name}:\n"
            f'    """L3: 精确属性断言 - 卡牌实例化失败."""\n'
            "    def test_card_identity(self, card):\n"
            f'        assert card.id == "{card_id}"\n'
        )

    name = getattr(instance, "name", "")

    from ptcg.core.card import PokemonCard, EnergyCard, TrainerCard

    lines: List[str] = []

    lines.append(f'class Test{set_code}{num}L3Structure:')
    lines.append(f'    """L3: 精确属性断言."""')
    lines.append('')
    lines.append('    def test_card_identity(self, card):')
    lines.append(f'        assert card.id == "{card_id}"')
    lines.append(f'        assert card.name == "{name}"')
    if hasattr(instance, "cardType"):
        ct = getattr(instance, "cardType", None)
        if ct is not None:
            lines.append(f'        assert card.cardType == CardType.{ct.name}')
    lines.append('')

    if isinstance(instance, PokemonCard):
        hp = getattr(instance, "hp", 0)
        lines.append('    def test_pokemon_attributes(self, card):')
        lines.append(f'        assert card.hp == {hp}')
        stage = getattr(instance, "stage", None)
        if stage is not None:
            from ptcg.core.enums import Stage
            lines.append(f'        assert card.stage == Stage.{stage.name}')
        pk_type = getattr(instance, "pokemonType", None)
        if pk_type is not None:
            from ptcg.core.enums import PokemonType
            lines.append(f'        assert card.pokemonType == PokemonType.{pk_type.name}')

        # retreat
        retreat = getattr(instance, "retreat", [])
        retreat_cost = [f"CardType.{e.name}" for e in retreat]
        lines.append(f'        assert card.retreat == [{", ".join(retreat_cost)}]')

        # weakness
        weakness = getattr(instance, "weakness", [])
        if weakness:
            weak_str = [f"CardType.{e.name}" for e in weakness]
            lines.append(f'        assert card.weakness == [{", ".join(weak_str)}]')

        # resistance
        resistance = getattr(instance, "resistance", [])
        if resistance:
            res_str = [f"CardType.{e.name}" for e in resistance]
            lines.append(f'        assert card.resistance == [{", ".join(res_str)}]')

        # evolveFrom
        evolve_from = getattr(instance, "evolveFrom", [])
        if evolve_from:
            ev_str = ", ".join(f'"{e}"' for e in evolve_from)
            lines.append(f'        assert card.evolveFrom == [{ev_str}]')

        # prize
        prize = getattr(instance, "prize", 1)
        lines.append(f'        assert card.prize == {prize}')

        # pokemonRule
        rule = getattr(instance, "pokemonRule", None)
        if rule is not None and hasattr(rule, "name") and rule.name != "NONE":
            from ptcg.core.enums import PokemonRule
            lines.append(f'        assert card.pokemonRule == PokemonRule.{rule.name}')

        lines.append('')

        # attacks
        attacks = getattr(instance, "attacks", [])
        if attacks:
            lines.append('    def test_attacks(self, card):')
            lines.append(f'        assert len(card.attacks) == {len(attacks)}')
            for i, atk in enumerate(attacks):
                atk_name = getattr(atk, "name", "")
                atk_damage = getattr(atk, "damage", 0)
                atk_cost = getattr(atk, "cost", [])
                cost_str = ", ".join(f"CardType.{e.name}" for e in atk_cost)
                lines.append(f'        assert card.attacks[{i}].name == "{atk_name}"')
                lines.append(f'        assert card.attacks[{i}].damage == {atk_damage}')
                lines.append(f'        assert card.attacks[{i}].cost == [{cost_str}]')
            lines.append('')

        # ability
        ability = getattr(instance, "ability", [])
        if ability:
            lines.append('    def test_abilities(self, card):')
            lines.append(f'        assert len(card.ability) == {len(ability)}')
            for i, ab in enumerate(ability):
                ab_name = getattr(ab, "name", "")
                lines.append(f'        assert card.ability[{i}].name == "{ab_name}"')
            lines.append('')

    elif isinstance(instance, EnergyCard):
        lines.append('    def test_energy_attributes(self, card):')
        et = getattr(instance, "energyType", None)
        if et is not None:
            from ptcg.core.enums import EnergyType
            lines.append(f'        assert card.energyType == EnergyType.{et.name}')
        provides = getattr(instance, "provides", [])
        if provides:
            prov_str = ", ".join(f"CardType.{e.name}" for e in provides)
            lines.append(f'        assert card.provides == [{prov_str}]')
        text = getattr(instance, "text", "")
        if text:
            escaped = text.replace('"', '\\"')
            lines.append(f'        assert card.text == "{escaped}"')
        lines.append('')

    elif isinstance(instance, TrainerCard):
        lines.append('    def test_trainer_attributes(self, card):')
        tt = getattr(instance, "trainerType", None)
        if tt is not None:
            from ptcg.core.enums import TrainerType
            lines.append(f'        assert card.trainerType == TrainerType.{tt.name}')
        text = getattr(instance, "text", "")
        if text:
            escaped = text.replace('"', '\\"')
            lines.append(f'        assert card.text == "{escaped}"')
        lines.append('')

    return "\n".join(lines)


def _generate_l5_class(set_code: str, num: str) -> str:
    """生成 L5 空占位 class。"""
    cls_name = f"Test{set_code}{num}L5EdgeCases"
    return (
        f"class {cls_name}:\n"
        f'    """L5: 边界条件 - TODO: 未实现真正的边界条件测试."""\n'
        "    pass\n"
    )



def _split_top_level_blocks(text: str) -> List[str]:
    """将 Python 源码按 top-level 定义（class/def）分割成独立的块。"""
    blocks: List[str] = []
    current_block: List[str] = []
    in_block = False
    for line in text.splitlines():
        if not line.strip():
            continue
        # 检查是否为 top-level 定义
        if line[0] != ' ' and line[0] != '\t':
            if current_block:
                blocks.append("\n".join(current_block))
                current_block = []
            current_block.append(line)
            in_block = True
        elif in_block:
            current_block.append(line)
    if current_block:
        blocks.append("\n".join(current_block))
    return blocks


def _extract_behavior_content(files: List[Path]) -> str:
    """从 behavior 文件提取 L4 测试 class 和所需 helper 函数。"""
    all_helpers: Dict[str, str] = {}
    all_classes: List[str] = []
    helper_count = 0

    for f in files:
        try:
            content = f.read_text(encoding="utf-8")
        except Exception:
            continue

        lines = content.splitlines()
        extracted_lines: List[str] = []
        skip_docstring = True  # 跳过文件头部 docstring

        i = 0
        while i < len(lines):
            stripped = lines[i].strip()

            # 跳过文件头部 docstring
            if skip_docstring and (stripped.startswith('"""') or stripped.startswith("'''")):
                while i < len(lines):
                    if '"""' in lines[i] or "'''" in lines[i]:
                        break
                    i += 1
                i += 1
                skip_docstring = False
                continue

            # 跳过 import、空行、CARD_ID、fixture
            if (stripped.startswith("import ") or stripped.startswith("from ")
                    or not stripped or stripped.startswith("CARD_ID")
                    or "@pytest.fixture" in stripped
                    or stripped == "def card():"):
                i += 1
                continue

            extracted_lines.append(lines[i])
            i += 1

        full = "\n".join(extracted_lines).strip()
        if not full:
            continue

        blocks = _split_top_level_blocks(full)
        for block in blocks:
            block = block.strip()
            if not block:
                continue
            if block.startswith("class "):
                all_classes.append(block)
            elif block.startswith("def "):
                name = re.match(r"def (\w+)", block)
                if name:
                    fn_name = name.group(1)
                    if fn_name not in all_helpers and helper_count < 3:
                        all_helpers[fn_name] = block
                        helper_count += 1

    result_parts = list(all_helpers.values()) + all_classes
    return "\n\n".join(result_parts)


def _extract_snapshot_content(files: List[Path]) -> str:
    """从 snapshot 文件提取 L6 测试 class（仅保留 class 定义，跳过 helper 函数）。"""
    all_classes: List[str] = []

    for f in files:
        try:
            content = f.read_text(encoding="utf-8")
        except Exception:
            continue

        lines = content.splitlines()
        extracted_lines: List[str] = []
        i = 0
        while i < len(lines):
            stripped = lines[i].strip()

            # 跳过文件头部 docstring（单行或多行）
            if i == 0:
                if stripped.startswith('"""') or stripped.startswith("'''"):
                    if stripped.count('"""') >= 2 or stripped.count("'''") >= 2:
                        # 单行 docstring
                        i += 1
                        continue
                    else:
                        # 多行 docstring
                        i += 1
                        while i < len(lines):
                            if '"""' in lines[i] or "'''" in lines[i]:
                                i += 1
                                break
                            i += 1
                        continue

            # 跳过 import、空行
            if stripped.startswith("import ") or stripped.startswith("from ") or not stripped:
                i += 1
                continue

            extracted_lines.append(lines[i])
            i += 1

        full = "\n".join(extracted_lines).strip()
        if not full:
            continue

        blocks = _split_top_level_blocks(full)
        for block in blocks:
            block = block.strip()
            if block.startswith("class "):
                all_classes.append(block)

    return "\n\n".join(all_classes)


def _generate_merged_file(
    card_id: str,
    set_code: str,
    num: str,
    card_name: str,
    source_files: Dict[str, List[Path]],
) -> str:
    """生成合并后的单文件内容。"""
    lines: List[str] = []
    all_imports: List[str] = []

    # ── 文件头 docstring ──
    lines.append(f'"""{card_name} ({card_id}) — L3-L6 测试."""')
    lines.append("")

    # ── 收集所有 import ──
    all_imports.append("import pytest")
    all_imports.append("from ptcg.core.card_registry import registry")

    # 从 card source 文件判断需要哪些 Enum 导入
    card_cls = _get_card_class(card_id)
    if card_cls is not None:
        try:
            instance = card_cls()
            from ptcg.core.card import PokemonCard, EnergyCard, TrainerCard

            enum_symbols: Set[str] = {"CardType"}

            if isinstance(instance, PokemonCard):
                from ptcg.core.enums import PokemonType, Stage
                enum_symbols.add("PokemonType")
                enum_symbols.add("Stage")
                pr = getattr(instance, "pokemonRule", None)
                if pr is not None and hasattr(pr, "name") and pr.name != "NONE":
                    from ptcg.core.enums import PokemonRule
                    enum_symbols.add("PokemonRule")

            if isinstance(instance, EnergyCard):
                from ptcg.core.enums import EnergyType
                enum_symbols.add("EnergyType")

            if isinstance(instance, TrainerCard):
                from ptcg.core.enums import TrainerType
                enum_symbols.add("TrainerType")

            all_imports.append(
                "from ptcg.core.enums import " + ", ".join(sorted(enum_symbols))
            )
        except Exception:
            pass

    # 从 behavior/snapshot 源文件收集 import
    for category in ["behavior", "snapshot"]:
        for f in source_files.get(category, []):
            try:
                content = f.read_text(encoding="utf-8")
                all_imports.extend(_extract_imports(content))
            except Exception:
                pass

    # 去重排序
    deduped = _deduplicate_imports(all_imports)
    lines.extend(deduped)
    lines.append("")

    # ── CARD_ID + fixture ──
    lines.append(f'CARD_ID = "{card_id}"')
    lines.append("")

    lines.append("")
    lines.append("@pytest.fixture")
    lines.append("def card():")
    lines.append('    cls = registry.get(CARD_ID)')
    lines.append('    if cls is None:')
    lines.append('        pytest.skip(f"{CARD_ID} not registered")')
    lines.append("    return cls()")
    lines.append("")

    # ── L3 精确属性断言 ──
    l3_content = _generate_l3_class(card_id, set_code, num)
    lines.append(l3_content)
    lines.append("")

    # ── L4 行为测试 ──
    behavior_files = source_files.get("behavior", [])
    if behavior_files:
        behavior_content = _extract_behavior_content(behavior_files)
        if behavior_content.strip():
            lines.append(behavior_content)
            lines.append("")

    # ── L5 + L6 快照测试 ──
    snapshot_files = source_files.get("snapshot", [])
    snapshot_content = ""
    if snapshot_files:
        snapshot_content = _extract_snapshot_content(snapshot_files)

    has_l5_in_snapshot = bool(
        snapshot_content and re.search(r"class Test.*L5(EdgeCases|[:\s])", snapshot_content)
    )
    if has_l5_in_snapshot:
        # 已有 L5 内容，直接添加所有 snapshot 内容（含 L5+L6）
        lines.append(snapshot_content)
    else:
        # 生成 L5 空占位
        l5_content = _generate_l5_class(set_code, num)
        lines.append(l5_content)
        if snapshot_content.strip():
            lines.append("")
            lines.append(snapshot_content)

    return "\n".join(lines)


def _get_card_name(card_id: str) -> str:
    """从 registry 获取卡牌名称。"""
    card_cls = _get_card_class(card_id)
    if card_cls is not None:
        try:
            instance = card_cls()
            name = getattr(instance, "name", "")
            if name:
                return name
        except Exception:
            pass
    return card_id


def process_set(set_code: str, dry_run: bool = False) -> int:
    """处理单个 set 的所有测试文件。返回处理卡牌数。"""
    groups = _group_test_files(set_code)
    if not groups:
        print(f"  [INFO] {set_code}: 无测试文件")
        return 0

    processed = 0
    for card_id, sources in sorted(groups.items()):
        # 从 card_id 提取 set 和 num
        try:
            s, n = card_id.split("-")
        except ValueError:
            print(f"  [WARN] 无效 card_id 格式: {card_id}")
            continue

        # 只处理当前 set
        if s.upper() != set_code:
            continue

        card_name = _get_card_name(card_id)
        output_name = f"test_{s.lower()}_{n}.py"
        output_path = GENERATED_DIR / set_code / output_name

        merged = _generate_merged_file(card_id, set_code, n, card_name, sources)

        # 收集要删除的文件
        files_to_delete: List[Path] = []
        for category_files in sources.values():
            files_to_delete.extend(category_files)

        if dry_run:
            print(f"  [DRY-RUN] {card_id} ({card_name})")
            print(f"    生成: {output_path.relative_to(PROJECT_ROOT)}")
            print(f"    删除 {len(files_to_delete)} 个旧文件:")
            for f in files_to_delete:
                print(f"      - {f.relative_to(PROJECT_ROOT)}")
        else:
            output_path.write_text(merged, encoding="utf-8")
            # 验证语法
            try:
                compile(merged, str(output_path), "exec")
            except SyntaxError as e:
                print(f"  [ERROR] {output_path.name}: 语法错误 — {e}")
                # 删除生成的文件并继续
                output_path.unlink(missing_ok=True)
                continue

            # 删除旧文件
            for f in files_to_delete:
                try:
                    f.unlink()
                except OSError as e:
                    print(f"  [WARN] 删除失败 {f.name}: {e}")

            print(f"  [OK] {card_id} ({card_name}) → {output_name} ({len(files_to_delete)} 旧文件已删除)")

        processed += 1

    return processed


def main():
    parser = argparse.ArgumentParser(description="合并 PTCG 卡牌测试文件")
    parser.add_argument("--dry-run", action="store_true", help="预览模式，不实际修改")
    parser.add_argument(
        "--set", dest="set_code", type=str, default="",
        help="只处理单个 set (如 ASR)"
    )
    parser.add_argument("--all", action="store_true", help="处理全部 set")
    args = parser.parse_args()

    if not args.set_code and not args.all:
        print("请指定 --set <SET> 或 --all")
        sys.exit(1)

    if args.all:
        sets_to_process = SET_DIRS
    else:
        sets_to_process = [args.set_code.upper()]

    total = 0
    for s in sets_to_process:
        print(f"\n=== 处理 {s} ===")
        count = process_set(s, dry_run=args.dry_run)
        total += count

    mode = "DRY-RUN" if args.dry_run else "DONE"
    print(f"\n=== {mode}: 共处理 {total} 张卡牌 ({len(sets_to_process)} 个 set) ===")


if __name__ == "__main__":
    main()
