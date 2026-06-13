"""构建语义提取输入包 preview —— CLI 入口。

从 apply_refetch_preview.py 生成的 application preview JSON 中挑选
prompt_ready=true 且 applied=true 的卡，输出结构化输入包 preview。

默认行为：
- 不联网
- 不调用 LLM
- 不写文件
- 不生成 semantic ops JSON
- 不生成最终 prompt
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from ptcg.data_sources.semantic_extraction_input import (
    _is_dangerous_output_path,
    build_semantic_extraction_input_preview,
)

SCHEMA_VERSION = "semantic_extraction_input_preview.v1"


# ---------------------------------------------------------------------------
# safety
# ---------------------------------------------------------------------------


def _validate_output_path(output_path: Path) -> list[str]:
    errors: list[str] = []
    msg = _is_dangerous_output_path(str(output_path))
    if msg:
        errors.append(msg)
    return errors


# ---------------------------------------------------------------------------
# core
# ---------------------------------------------------------------------------


def _load_application_preview(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _print_summary(result: dict[str, Any]) -> None:
    meta = result["meta"]
    summary = result["summary"]
    cards = result.get("cards", [])

    print("=" * 60)
    print("  语义提取输入包 preview 完成")
    print("=" * 60)
    print(f"  network_enabled        : {meta['network_enabled']}")
    print(f"  calls_llm              : {meta['calls_llm']}")
    print(f"  writes_semantic_ops_json: {meta['writes_semantic_ops_json']}")
    print(f"  writes_prompt           : {meta['writes_prompt']}")
    print("-" * 60)
    print(f"  input_application_count : {summary['input_application_count']}")
    print(f"  selected_count          : {summary['selected_count']}")
    print(f"  ready_count             : {summary['ready_count']}")
    print(f"  not_ready_count         : {summary['not_ready_count']}")
    print(f"  errors                  : {summary['error_count']}")
    print(f"  warnings                : {summary['warning_count']}")
    print("=" * 60)

    for card in cards:
        key = card["card_key"]
        task = card.get("semantic_extraction_task", {})
        available_ops = card.get("known_runtime_support", {}).get("available_ops", [])
        text = card.get("normalized_text", {})
        has_text = bool(text.get("full_text_zh") or text.get("trainer_text_zh"))
        print(
            f"  [{key}] task={task.get('task_type')}, "
            f"text={'OK' if has_text else 'MISSING'}, "
            f"ops={len(available_ops)}"
        )

    print("=" * 60)


def _write_output(result: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    print(f"[INFO] semantic extraction input preview written to {output_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="从 application preview JSON 构建语义提取输入包 preview。",
    )
    parser.add_argument(
        "--input-application-preview",
        type=Path,
        required=True,
        dest="input_application_preview",
        metavar="PATH",
        help="apply_refetch_preview.py 生成的 application preview JSON 文件",
    )
    parser.add_argument(
        "--card-key",
        type=str,
        action="append",
        default=None,
        dest="card_key",
        metavar="KEY",
        help="只处理指定 card_key（可重复）。",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        dest="limit",
        metavar="N",
        help="最多处理 N 张卡。",
    )
    parser.add_argument(
        "--output-input-preview",
        type=Path,
        default=None,
        dest="output_input_preview",
        metavar="PATH",
        help="可选。输出 semantic extraction input preview JSON。不传则不写文件。",
    )
    parser.add_argument(
        "--include-op-inventory",
        action="store_true",
        default=True,
        dest="include_op_inventory",
        help="包含当前支持的 semantic op 清单（默认启用）。",
    )
    parser.add_argument(
        "--fail-on-not-ready",
        action="store_true",
        default=False,
        dest="fail_on_not_ready",
        help="若选中的卡中存在不满足 prompt_ready 的，exit code 非 0。",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    # ------------------------------------------------------------------
    # 0. validate input
    # ------------------------------------------------------------------
    if not args.input_application_preview.exists():
        print(f"[ERROR] 找不到文件: {args.input_application_preview}", file=sys.stderr)
        return 1

    # ------------------------------------------------------------------
    # 1. validate output path safety
    # ------------------------------------------------------------------
    output_path: Path | None = args.output_input_preview
    if output_path is not None:
        errors = _validate_output_path(output_path)
        if errors:
            for e in errors:
                print(f"[ERROR] {e}", file=sys.stderr)
            return 1

    # ------------------------------------------------------------------
    # 2. load application preview JSON
    # ------------------------------------------------------------------
    try:
        source = _load_application_preview(args.input_application_preview)
    except FileNotFoundError:
        print(f"[ERROR] 找不到文件: {args.input_application_preview}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"[ERROR] JSON 解析失败: {exc}", file=sys.stderr)
        return 1

    # ------------------------------------------------------------------
    # 3. build semantic extraction input preview
    # ------------------------------------------------------------------
    result = build_semantic_extraction_input_preview(
        source,
        card_keys=args.card_key,
        limit=args.limit,
        include_op_inventory=args.include_op_inventory,
        fail_on_not_ready=args.fail_on_not_ready,
    )

    # ------------------------------------------------------------------
    # 4. output
    # ------------------------------------------------------------------
    _print_summary(result)

    if output_path is not None:
        _write_output(result, output_path)

    # ------------------------------------------------------------------
    # 5. fail-on-not-ready
    # ------------------------------------------------------------------
    if args.fail_on_not_ready:
        if result.get("meta", {}).get("fail_on_not_ready_triggered"):
            print("[ERROR] --fail-on-not-ready: 存在未 ready 的卡。", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
