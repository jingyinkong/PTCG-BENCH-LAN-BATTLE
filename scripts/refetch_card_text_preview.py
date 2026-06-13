"""Controlled refetch preview command.

串接 Phase 7D–7G 的产物，生成 refetch preview 输出。

默认行为（无 --network，无 --output-preview）：
- 读取本地 normalized records
- 生成 refetch plan 与 dry-run requests
- 打印计划摘要到 stdout
- 不联网、不写文件

--network 显式开启时才允许真实网络请求。
--output-preview 显式指定时才写 preview 文件。
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from ptcg.data_sources.normalized_card_text import build_normalized_records
from ptcg.data_sources.text_refetch_dry_run import build_refetch_dry_run_requests
from ptcg.data_sources.text_refetch_plan import build_text_refetch_plan
from ptcg.data_sources.tcg_mik_refetch_client import TcgMikRefetchClient

# ---------------------------------------------------------------------------
# constants
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_VERSION = "refetch-preview-v1"

_TCG_MIK_DETAIL_URL = "https://tcg.mik.moe/api/v3/card/card-detail"
_REQUEST_TIMEOUT = 15

# 禁止被覆盖的路径文件名
_FORBIDDEN_OUTPUT_NAMES = {
    "card_chinese_data.json",
    "card_data_cache.json",
    "normalized_card_text.json",
    "data/normalized_card_text.json",
}


# ---------------------------------------------------------------------------
# real fetcher
# ---------------------------------------------------------------------------


def make_tcg_mik_fetcher(
    timeout: int = _REQUEST_TIMEOUT,
) -> Callable[[dict[str, Any]], dict[str, Any]]:
    """构建真实 tcg.mik.moe card-detail fetcher。

    仅在 --network 开启时调用。对 lookup_strategy != detail_by_source_ids
    的请求返回 unsupported_lookup_strategy 错误。
    """
    import requests as _requests  # 仅 --network 时引入

    def _fetcher(dry_run_request: dict[str, Any]) -> dict[str, Any]:
        strategy = dry_run_request.get("lookup_strategy", "")
        if strategy != "detail_by_source_ids":
            return {
                "_error": "unsupported_real_network_locator",
                "_detail": f"lookup_strategy={strategy} not implemented for real network",
            }

        lookup: dict[str, Any] = dry_run_request.get("lookup", {})
        set_code_cn = lookup.get("set_code_cn") or lookup.get("setCodeEn")
        card_index_cn = lookup.get("card_index_cn") or lookup.get("cardIndexEn")

        if not set_code_cn or not card_index_cn:
            return {
                "_error": "missing_locator_params",
                "_detail": "set_code_cn and card_index_cn required for detail_by_source_ids",
            }

        try:
            resp = _requests.post(
                _TCG_MIK_DETAIL_URL,
                json={"setCode": str(set_code_cn), "cardIndex": str(card_index_cn)},
                timeout=timeout,
                headers={"User-Agent": "ptcg-refetch-preview/1.0"},
            )
            resp.raise_for_status()
            body = resp.json()
            # tcg.mik.moe wraps success in {"code": 200, "data": {...}}
            if isinstance(body, dict) and body.get("code") == 200 and "data" in body:
                return body["data"]
            return body
        except _requests.Timeout:
            return {"_error": "request_timeout", "_detail": f"timeout after {timeout}s"}
        except _requests.RequestException as exc:
            return {"_error": "request_failed", "_detail": str(exc)}

    return _fetcher


# ---------------------------------------------------------------------------
# safety
# ---------------------------------------------------------------------------

_RESERVED_FILES_IN_ROOT = {
    "card_chinese_data.json",
    "card_data_cache.json",
    "normalized_card_text.json",
    "deck_data.json",
}


def _validate_output_path(output_path: Path) -> list[str]:
    """检查 output path 是否安全。返回错误列表，空列表表示安全。"""
    errors: list[str] = []

    name = output_path.name
    # 精确匹配禁止文件名
    if name in _FORBIDDEN_OUTPUT_NAMES:
        errors.append(
            f"禁止覆盖受保护的文件: {name}。请使用 --output-preview 指定包含 'preview' 的文件名。"
        )

    # 仓库根目录下的保留文件名
    if output_path.is_absolute():
        try:
            relative = output_path.relative_to(REPO_ROOT)
            if str(relative) in _RESERVED_FILES_IN_ROOT or output_path.name in _RESERVED_FILES_IN_ROOT:
                errors.append(
                    f"禁止写入仓库根目录下的保留文件: {name}"
                )
        except ValueError:
            # 不在仓库根目录下，不检查
            pass
    elif output_path.parent == Path(".") and name in _RESERVED_FILES_IN_ROOT:
        errors.append(
            f"禁止写入仓库根目录下的保留文件: {name}"
        )

    return errors


# ---------------------------------------------------------------------------
# pipeline
# ---------------------------------------------------------------------------


def _build_preview(
    records: dict[str, dict[str, Any]],
    card_keys: list[str] | None,
    limit: int,
    network_enabled: bool,
    fetcher: Callable[[dict[str, Any]], dict[str, Any]] | None,
) -> dict[str, Any]:
    """构建 preview 数据结构。"""
    # 1. build plan
    plan = build_text_refetch_plan(records)

    # 2. filter by card_key
    if card_keys:
        key_set = set(card_keys)
        plan = [p for p in plan if p["card_key"] in key_set]

    # 3. build dry-run requests
    requests = build_refetch_dry_run_requests(plan)
    requests = requests[:limit]

    # 4. compute blocking
    blocking_count = sum(
        1 for r in requests if not r.get("can_refetch") or r.get("blocking_issues")
    )

    # 5. results
    results: list[dict[str, Any]] = []
    client = TcgMikRefetchClient(fetcher=fetcher, network_enabled=network_enabled)
    for req in requests:
        result = client.fetch_detail_for_request(req)
        results.append(result)

    # 6. summary
    summary = {
        "total_records": len(records),
        "planned_count": len(plan),
        "request_count": len(requests),
        "result_count": len(results),
        "blocking_count": blocking_count,
    }

    return {
        "meta": {
            "dry_run": not network_enabled or fetcher is None,
            "network_enabled": network_enabled,
            "will_write_files": False,
            "writes_original_cache": False,
            "writes_normalized_cache": False,
            "schema_version": SCHEMA_VERSION,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
        "summary": summary,
        "requests": requests,
        "results": results,
    }


# ---------------------------------------------------------------------------
# output helpers
# ---------------------------------------------------------------------------


def _print_summary(preview: dict[str, Any]) -> None:
    """打印摘要到 stdout。"""
    meta = preview["meta"]
    summary = preview["summary"]

    print("=" * 60)
    print("  Refetch Card Text Preview")
    print("=" * 60)
    print(f"  network_enabled      : {meta['network_enabled']}")
    print(f"  dry_run              : {meta['dry_run']}")
    print(f"  writes_original_cache: {meta['writes_original_cache']}")
    print(f"  writes_normalized_cache: {meta['writes_normalized_cache']}")
    print(f"  generated_at         : {meta['generated_at']}")
    print("-" * 60)
    print(f"  total_records  : {summary['total_records']}")
    print(f"  planned_count  : {summary['planned_count']}")
    print(f"  request_count  : {summary['request_count']}")
    print(f"  result_count   : {summary['result_count']}")
    print(f"  blocking_count : {summary['blocking_count']}")
    print("=" * 60)

    for r in preview["results"]:
        card_key = r.get("card_key", "?")
        errors = r.get("errors", [])
        patch_keys = list(r.get("normalized_patch_preview", {}).keys())
        status = "OK" if not errors else ", ".join(errors)
        print(f"  [{status}] {card_key} | patch: {patch_keys}")
    print("=" * 60)


def _write_preview(preview: dict[str, Any], output_path: Path) -> None:
    """写入 preview JSON 文件。"""
    preview["meta"]["will_write_files"] = True
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(preview, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    print(f"[INFO] preview written to {output_path}")


# ---------------------------------------------------------------------------
# CLI entry
# ---------------------------------------------------------------------------


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="受控 refetch preview 命令 —— 默认不联网、不写文件。",
    )
    parser.add_argument(
        "--card-key",
        action="append",
        default=None,
        dest="card_keys",
        metavar="KEY",
        help="只处理指定卡牌 (可重复使用，如 --card-key TWM-145 --card-key SSH-178)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="最多处理多少条 refetch request (默认: 10)",
    )
    parser.add_argument(
        "--network",
        action="store_true",
        default=False,
        help="显式允许真实网络请求 (默认: 不联网)",
    )
    parser.add_argument(
        "--output-preview",
        type=Path,
        default=None,
        dest="output_preview",
        metavar="PATH",
        help="写入 preview JSON 的路径 (未提供则不写文件)",
    )
    parser.add_argument(
        "--fail-on-blocking",
        action="store_true",
        default=False,
        dest="fail_on_blocking",
        help="如果 plan 中有 blocking 条目则 exit code 非 0",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    # ------------------------------------------------------------------
    # 0. validate output path safety
    # ------------------------------------------------------------------
    output_path: Path | None = args.output_preview
    if output_path is not None:
        errors = _validate_output_path(output_path)
        if errors:
            for err in errors:
                print(f"[ERROR] {err}", file=sys.stderr)
            return 1

    # ------------------------------------------------------------------
    # 1. build normalized records
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
    # 2. construct fetcher
    # ------------------------------------------------------------------
    fetcher: Callable[[dict[str, Any]], dict[str, Any]] | None = None
    network_enabled: bool = args.network

    if network_enabled:
        fetcher = make_tcg_mik_fetcher()

    # ------------------------------------------------------------------
    # 3. build preview
    # ------------------------------------------------------------------
    preview = _build_preview(
        records=records,
        card_keys=args.card_keys,
        limit=args.limit,
        network_enabled=network_enabled,
        fetcher=fetcher,
    )

    # ------------------------------------------------------------------
    # 4. output
    # ------------------------------------------------------------------
    if output_path is not None:
        _write_preview(preview, output_path)
    elif network_enabled:
        print("[WARN] --network 已启用但没有 --output-preview，结果仅输出到 stdout，不会写文件。")

    _print_summary(preview)

    # ------------------------------------------------------------------
    # 5. fail-on-blocking
    # ------------------------------------------------------------------
    if args.fail_on_blocking:
        blocking_count = preview["summary"]["blocking_count"]
        if blocking_count > 0:
            print(f"[FAIL] blocking_count={blocking_count} > 0", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
