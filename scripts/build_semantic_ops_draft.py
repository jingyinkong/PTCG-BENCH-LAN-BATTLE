"""构建单卡 semantic ops draft preview —— CLI 入口。

从 Phase 7S build_semantic_extraction_prompt.py 生成的 prompt preview JSON 中
提取指定 card_key 的数据，生成 semantic ops draft preview。

默认行为：
- 不联网
- 不调用 LLM
- 不写文件
- 不生成正式 semantic ops JSON
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from ptcg.data_sources.semantic_ops_draft import (
    build_semantic_ops_draft_preview,
)

SCHEMA_VERSION = "semantic_ops_draft_preview.v1"

# ---------------------------------------------------------------------------
# 危险输出路径名单（禁止写入受保护的文件）
# ---------------------------------------------------------------------------

_FORBIDDEN_OUTPUT_NAMES: set[str] = {
    "card_chinese_data.json",
    "card_data_cache.json",
    "normalized_card_text.json",
    "semantic_ops.json",
    "ops.json",
}

_FORBIDDEN_ENDS_WITH: tuple[str, ...] = (
    "semantic_ops.json",
)

_FORBIDDEN_EXACT_NAMES: set[str] = {
    "prompt.md",
    "prompt.txt",
    "prompt.json",
    "final_prompt.md",
    "final_prompt.txt",
    "final_prompt.json",
}


def _is_dangerous_output_path(path: str) -> str | None:
    """检查输出路径是否危险。返回错误消息或 None（安全）。"""
    name = os.path.basename(path)

    if name in _FORBIDDEN_OUTPUT_NAMES:
        return f"禁止写入受保护的文件: {name}"

    norm_path = path.replace("\\", "/")

    if norm_path.startswith("data/") and name == "normalized_card_text.json":
        return "禁止写入 data/normalized_card_text.json"

    if "normalized_card_text.json" in norm_path:
        return f"禁止写入任何 normalized_card_text.json 文件: {path}"

    if name.endswith(_FORBIDDEN_ENDS_WITH):
        return f"禁止写入 semantic_ops.json: {path}"

    if norm_path.startswith("prompts/"):
        return f"禁止写入 prompts/ 目录: {path}"

    if name.lower() in _FORBIDDEN_EXACT_NAMES:
        return f"禁止写入 prompt 相关文件: {name}"

    # 禁止写入 ptcg/cards/ 和 ptcg/core/
    if norm_path.startswith("ptcg/cards/"):
        return f"禁止写入 ptcg/cards/ 目录: {path}"

    if norm_path.startswith("ptcg/core/"):
        return f"禁止写入 ptcg/core/ 目录: {path}"

    return None


def _validate_output_path(output_path: Path) -> list[str]:
    errors: list[str] = []
    msg = _is_dangerous_output_path(str(output_path))
    if msg:
        errors.append(msg)
    return errors


# ---------------------------------------------------------------------------
# core
# ---------------------------------------------------------------------------


def _load_prompt_preview(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _print_summary(result: dict[str, Any]) -> None:
    meta = result["meta"]
    card_key = result["card_key"]
    draft_ready = result["draft_ready"]
    needs_review = result.get("unsupported_or_needs_manual_review", False)
    reasons = result.get("unsupported_reasons", [])
    effect = result.get("effect_summary", "")
    candidate_ops = result.get("candidate_ops_sequence", [])
    risk_notes = result.get("risk_notes", [])

    print("=" * 60)
    print("  单卡 semantic ops draft preview 完成")
    print("=" * 60)
    print(f"  card_key                : {card_key}")
    print(f"  draft_ready             : {draft_ready}")
    print(f"  calls_llm               : {meta['calls_llm']}")
    print(f"  network_enabled         : {meta['network_enabled']}")
    print(f"  writes_semantic_ops_json: {meta['writes_semantic_ops_json']}")
    print(f"  writes_cards            : {meta['writes_cards']}")
    print(f"  writes_core             : {meta['writes_core']}")
    print(f"  needs_manual_review     : {needs_review}")
    print("-" * 60)

    if effect:
        print(f"  effect_summary           : {effect}")

    if candidate_ops:
        print(f"  candidate_ops_sequence   : {len(candidate_ops)} ops")
        for i, op in enumerate(candidate_ops, 1):
            op_type = op["op_type"]
            purpose = op.get("purpose", "")
            draft_args = op.get("draft_args", {})
            count = draft_args.get("count", "N/A")
            print(f"    [{i}] {op_type} (count={count}) - {purpose}")

    if reasons:
        print(f"  unsupported_reasons ({len(reasons)}):")
        for r in reasons:
            print(f"    - {r}")

    if risk_notes:
        print(f"  risk_notes ({len(risk_notes)}):")
        for r in risk_notes:
            print(f"    - {r}")

    if result.get("error"):
        print(f"  [ERROR] {result['error']}")

    print("=" * 60)


def _write_output(result: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    print(f"[INFO] draft preview written to {output_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="从 Phase 7S prompt preview JSON 生成单卡 semantic ops draft preview。",
    )
    parser.add_argument(
        "--input-prompt-preview",
        type=Path,
        required=True,
        dest="input_prompt_preview",
        metavar="PATH",
        help="Phase 7S build_semantic_extraction_prompt.py 生成的 prompt preview JSON 文件",
    )
    parser.add_argument(
        "--card-key",
        type=str,
        required=True,
        dest="card_key",
        metavar="KEY",
        help="目标 card_key（本阶段只支持单卡）。",
    )
    parser.add_argument(
        "--output-draft-preview",
        type=Path,
        default=None,
        dest="output_draft_preview",
        metavar="PATH",
        help="可选。输出 draft preview JSON。不传则不写文件。",
    )
    parser.add_argument(
        "--fail-on-unsupported",
        action="store_true",
        default=False,
        dest="fail_on_unsupported",
        help="如果检测到 unsupported_or_needs_manual_review=true，则 exit code 非 0。",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    # ------------------------------------------------------------------
    # 0. validate input
    # ------------------------------------------------------------------
    if not args.input_prompt_preview.exists():
        print(f"[ERROR] 找不到文件: {args.input_prompt_preview}", file=sys.stderr)
        return 1

    if not args.card_key:
        print("[ERROR] --card-key 为必填参数。", file=sys.stderr)
        return 1

    # ------------------------------------------------------------------
    # 1. validate output path safety
    # ------------------------------------------------------------------
    output_path: Path | None = args.output_draft_preview
    if output_path is not None:
        errors = _validate_output_path(output_path)
        if errors:
            for e in errors:
                print(f"[ERROR] {e}", file=sys.stderr)
            return 1

    # ------------------------------------------------------------------
    # 2. load prompt preview JSON
    # ------------------------------------------------------------------
    try:
        source = _load_prompt_preview(args.input_prompt_preview)
    except json.JSONDecodeError as exc:
        print(f"[ERROR] JSON 解析失败: {exc}", file=sys.stderr)
        return 1

    # ------------------------------------------------------------------
    # 3. build draft preview
    # ------------------------------------------------------------------
    result = build_semantic_ops_draft_preview(
        source,
        card_key=args.card_key,
    )

    # ------------------------------------------------------------------
    # 4. output
    # ------------------------------------------------------------------
    _print_summary(result)

    if output_path is not None:
        _write_output(result, output_path)

    # ------------------------------------------------------------------
    # 5. fail-on-unsupported
    # ------------------------------------------------------------------
    if args.fail_on_unsupported:
        if result.get("unsupported_or_needs_manual_review"):
            print(
                "[ERROR] --fail-on-unsupported: 卡牌需要 manual review。",
                file=sys.stderr,
            )
            return 1

    # error in result
    if result.get("error"):
        print(f"[ERROR] {result['error']}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
