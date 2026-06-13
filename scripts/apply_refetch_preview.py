"""Apply refetch preview results to normalized records (dry-run, in-memory).

将 refetch_card_text_preview.py 生成的 preview JSON 中的 results 应用到
normalized records 的内存预览中，并输出 application report。

默认行为：
- 纯 in-memory dry-run
- 不联网
- 不写任何文件
- 不覆盖任何原始 JSON
- 不生成正式 normalized JSON
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

from ptcg.data_sources.normalized_card_text import build_normalized_records
from ptcg.data_sources.normalized_patch_application import (
    apply_refetch_result_to_normalized_record,
)

# ---------------------------------------------------------------------------
# constants
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_VERSION = "normalized_patch_application_preview.v1"

# 禁止被覆盖的路径文件名
_FORBIDDEN_OUTPUT_NAMES = {
    "card_chinese_data.json",
    "card_data_cache.json",
    "normalized_card_text.json",
}

_KILLSWITCH_NAMES = {
    "card_chinese_data.json",
    "card_data_cache.json",
    "normalized_card_text.json",
}


# ---------------------------------------------------------------------------
# safety
# ---------------------------------------------------------------------------


def _validate_output_path(output_path: Path) -> list[str]:
    """检查 output path 是否安全。返回错误列表，空列表表示安全。"""
    errors: list[str] = []

    name = output_path.name
    if name in _FORBIDDEN_OUTPUT_NAMES:
        errors.append(
            f"禁止覆盖受保护的文件: {name}"
        )
        return errors

    # 同时也检查文件名等于禁止列表中的任意项
    if name in _KILLSWITCH_NAMES:
        errors.append(
            f"禁止写入受保护的文件名: {name}"
        )
        return errors

    # 路径解析后检查
    if output_path.is_absolute():
        try:
            relative = output_path.relative_to(REPO_ROOT)
            if str(relative) in ("card_chinese_data.json", "card_data_cache.json"):
                errors.append(
                    f"禁止写入仓库根目录下的保留文件: {name}"
                )
        except ValueError:
            # 不在仓库下，安全
            pass
    elif str(output_path).replace("\\", "/").startswith("data/") and name == "normalized_card_text.json":
        errors.append(
            f"禁止写入 data/normalized_card_text.json"
        )
    # 检查任何包含 normalized_card_text.json 的路径
    if "normalized_card_text.json" in str(output_path):
        errors.append(
            f"禁止写入任何 normalized_card_text.json 文件: {output_path}"
        )

    return errors


# ---------------------------------------------------------------------------
# core logic
# ---------------------------------------------------------------------------


def _build_application_report(
    records: dict[str, dict[str, Any]],
    results: list[dict[str, Any]],
    *,
    card_keys: list[str] | None,
    limit: int,
    allow_overwrite: bool,
) -> dict[str, Any]:
    """对每个 refetch result 应用 patch，返回 application report。"""
    applications: list[dict[str, Any]] = []
    processed_count = 0
    applied_count = 0
    skipped_count = 0
    error_count = 0
    warning_count = 0

    # filter by card_key
    if card_keys:
        key_set = set(card_keys)
        target_results = [r for r in results if r.get("card_key") in key_set]
    else:
        target_results = list(results)

    # apply limit
    target_results = target_results[:limit]

    for refetch_result in target_results:
        processed_count += 1
        card_key = refetch_result.get("card_key", "???")

        # find matching normalized record
        record = records.get(card_key)
        if record is None:
            app_result: dict[str, Any] = {
                "card_key": card_key,
                "applied": False,
                "updated_record_preview": {},
                "application_report": {
                    "applied_fields": [],
                    "skipped_fields": [],
                    "warnings": [],
                    "errors": ["normalized_record_not_found"],
                    "quality_flag_updates": {},
                    "provenance_updates": {},
                },
            }
            error_count += 1
            applications.append(app_result)
            continue

        # apply
        try:
            result = apply_refetch_result_to_normalized_record(
                record,
                refetch_result,
                allow_overwrite=allow_overwrite,
            )
        except Exception as exc:
            app_result = {
                "card_key": card_key,
                "applied": False,
                "updated_record_preview": copy.deepcopy(record) if record else {},
                "application_report": {
                    "applied_fields": [],
                    "skipped_fields": [],
                    "warnings": [],
                    "errors": [f"application_exception: {exc}"],
                    "quality_flag_updates": {},
                    "provenance_updates": {},
                },
            }
            error_count += 1
            applications.append(app_result)
            continue

        report = result.application_report
        app_dict = result.asdict()

        if result.applied:
            applied_count += 1
        else:
            skipped_count += 1

        if report.get("errors"):
            error_count += len(report["errors"])
        if report.get("warnings"):
            warning_count += len(report["warnings"])

        applications.append(app_dict)

    summary = {
        "input_result_count": len(results),
        "processed_count": processed_count,
        "applied_count": applied_count,
        "skipped_count": skipped_count,
        "error_count": error_count,
        "warning_count": warning_count,
    }

    return {
        "summary": summary,
        "applications": applications,
    }


# ---------------------------------------------------------------------------
# output helpers
# ---------------------------------------------------------------------------


def _print_summary(report: dict[str, Any], *, allow_overwrite: bool, input_preview: str) -> None:
    """打印中文摘要到 stdout。"""
    meta_keys = {
        "dry_run": True,
        "network_enabled": False,
        "writes_original_cache": False,
        "writes_normalized_cache": False,
        "writes_formal_normalized_json": False,
        "allow_overwrite": allow_overwrite,
        "input_preview": input_preview,
        "schema_version": SCHEMA_VERSION,
    }
    summary = report["summary"]

    print("=" * 60)
    print("  补抓 patch application preview 完成")
    print("=" * 60)
    print(f"  dry_run                : {meta_keys['dry_run']}")
    print(f"  network_enabled        : {meta_keys['network_enabled']}")
    print(f"  writes_original_cache  : {meta_keys['writes_original_cache']}")
    print(f"  writes_normalized_cache: {meta_keys['writes_normalized_cache']}")
    print(f"  allow_overwrite        : {meta_keys['allow_overwrite']}")
    print("-" * 60)
    print(f"  input_result_count : {summary['input_result_count']}")
    print(f"  processed          : {summary['processed_count']}")
    print(f"  applied            : {summary['applied_count']}")
    print(f"  skipped            : {summary['skipped_count']}")
    print(f"  errors             : {summary['error_count']}")
    print(f"  warnings           : {summary['warning_count']}")
    print("=" * 60)

    for app in report["applications"]:
        card_key = app["card_key"]
        applied = app["applied"]
        report_fields = app.get("application_report", {})
        applied_fields = report_fields.get("applied_fields", [])
        skipped_fields = report_fields.get("skipped_fields", [])
        errors = report_fields.get("errors", [])

        print(
            f"  [{card_key}] applied={applied}, "
            f"applied_fields={len(applied_fields)}, "
            f"skipped_fields={len(skipped_fields)}, "
            f"errors={len(errors)}"
        )

    print("=" * 60)

    # errors summary
    if summary["error_count"] > 0:
        print(f"\n[WARN] {summary['error_count']} error(s) detected.")

    if summary["warning_count"] > 0:
        print(f"[WARN] {summary['warning_count']} warning(s) detected.")


def _write_output(report: dict[str, Any], output_path: Path, *, allow_overwrite: bool, input_preview: str) -> None:
    """写入 application preview/report JSON。"""
    output = {
        "meta": {
            "dry_run": True,
            "network_enabled": False,
            "writes_original_cache": False,
            "writes_normalized_cache": False,
            "writes_formal_normalized_json": False,
            "input_preview": input_preview,
            "allow_overwrite": allow_overwrite,
            "schema_version": SCHEMA_VERSION,
        },
        "summary": report["summary"],
        "applications": report["applications"],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(output, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    print(f"[INFO] application preview written to {output_path}")


# ---------------------------------------------------------------------------
# CLI entry
# ---------------------------------------------------------------------------


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="应用 refetch preview JSON 到 normalized records (纯内存 dry-run，不写文件)。",
    )
    parser.add_argument(
        "--input-preview",
        type=Path,
        required=True,
        dest="input_preview",
        metavar="PATH",
        help="refetch_card_text_preview.py 生成的 preview JSON 文件路径",
    )
    parser.add_argument(
        "--card-key",
        action="append",
        default=None,
        dest="card_keys",
        metavar="KEY",
        help="只应用指定卡牌 (可重复使用，如 --card-key TWM-145 --card-key SSH-178)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="最多处理 N 条 results (默认: 0 表示处理全部)",
    )
    parser.add_argument(
        "--allow-overwrite",
        action="store_true",
        default=False,
        dest="allow_overwrite",
        help="允许覆盖已有字段 (传给 apply_refetch_result_to_normalized_record)",
    )
    parser.add_argument(
        "--output-application-preview",
        type=Path,
        default=None,
        dest="output_application_preview",
        metavar="PATH",
        help="写入 application preview JSON 的路径 (不传则不写文件)",
    )
    parser.add_argument(
        "--fail-on-errors",
        action="store_true",
        default=False,
        dest="fail_on_errors",
        help="如果任何 application result applied=false 或 errors 非空则 exit code=1",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    # ------------------------------------------------------------------
    # 0. validate input
    # ------------------------------------------------------------------
    input_preview_path: Path = args.input_preview
    if not input_preview_path.exists():
        print(f"[ERROR] 输入文件不存在: {input_preview_path}", file=sys.stderr)
        return 1

    # ------------------------------------------------------------------
    # 1. validate output path safety
    # ------------------------------------------------------------------
    output_path: Path | None = args.output_application_preview
    if output_path is not None:
        errors = _validate_output_path(output_path)
        if errors:
            for err in errors:
                print(f"[ERROR] {err}", file=sys.stderr)
            return 1

    # ------------------------------------------------------------------
    # 2. load input preview JSON
    # ------------------------------------------------------------------
    try:
        raw = input_preview_path.read_text(encoding="utf-8")
        input_preview = json.loads(raw)
    except Exception as exc:
        print(f"[ERROR] 无法读取或解析 input preview JSON: {exc}", file=sys.stderr)
        return 1

    results: list[dict[str, Any]] = input_preview.get("results", [])
    if not results:
        print("[WARN] input preview 中没有 results，无需处理。")
        return 0

    # ------------------------------------------------------------------
    # 3. build normalized records (in-memory, no network)
    # ------------------------------------------------------------------
    chinese_data = REPO_ROOT / "card_chinese_data.json"
    cache_data = REPO_ROOT / "card_data_cache.json"
    cards_root = REPO_ROOT / "ptcg" / "cards"

    if not chinese_data.exists():
        print(f"[ERROR] 缺少 card_chinese_data.json: {chinese_data}", file=sys.stderr)
        return 1
    if not cache_data.exists():
        print(f"[ERROR] 缺少 card_data_cache.json: {cache_data}", file=sys.stderr)
        return 1

    records = build_normalized_records(chinese_data, cache_data, cards_root)

    # ------------------------------------------------------------------
    # 4. apply results
    # ------------------------------------------------------------------
    limit = args.limit if args.limit > 0 else len(results)
    allow_overwrite: bool = args.allow_overwrite

    report = _build_application_report(
        records=records,
        results=results,
        card_keys=args.card_keys,
        limit=limit,
        allow_overwrite=allow_overwrite,
    )

    # ------------------------------------------------------------------
    # 5. output
    # ------------------------------------------------------------------
    _print_summary(
        report,
        allow_overwrite=allow_overwrite,
        input_preview=str(input_preview_path),
    )

    if output_path is not None:
        _write_output(
            report,
            output_path,
            allow_overwrite=allow_overwrite,
            input_preview=str(input_preview_path),
        )

    # ------------------------------------------------------------------
    # 6. fail-on-errors
    # ------------------------------------------------------------------
    if args.fail_on_errors:
        fails = [
            app for app in report["applications"]
            if not app["applied"] or app.get("application_report", {}).get("errors")
        ]
        if fails:
            print(f"[FAIL] {len(fails)} application(s) have applied=false or non-empty errors.", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
