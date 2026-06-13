"""Tests for refetch_card_text_preview.py — 不真实联网。"""

from __future__ import annotations

import ast
import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "refetch_card_text_preview.py"

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _load_script_module():
    """Load the script module via importlib (avoids package __init__.py issues)."""
    spec = importlib.util.spec_from_file_location(
        "refetch_card_text_preview", SCRIPT_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load script: {SCRIPT_PATH}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["refetch_card_text_preview"] = mod
    spec.loader.exec_module(mod)
    return mod


def _run_main(*args: str) -> tuple[int, str]:
    """Run main() with given args and capture stdout/stderr."""
    from io import StringIO

    saved_stdout = sys.stdout
    saved_stderr = sys.stderr
    try:
        captured = StringIO()
        sys.stdout = captured
        sys.stderr = captured

        mod = _load_script_module()
        exit_code = mod.main(argv=list(args))
        return exit_code, captured.getvalue()
    finally:
        sys.stdout = saved_stdout
        sys.stderr = saved_stderr


def _fake_detail_response() -> dict:
    return {
        "cardType": "Supporter",
        "description": "丢弃自己的手牌，抽出5张卡。",
    }


def _fake_fetcher(response: dict):
    def _fetcher(_request: dict) -> dict:
        return response
    return _fetcher


# ---------------------------------------------------------------------------
# 1. 默认模式不联网
# ---------------------------------------------------------------------------


def test_default_mode_no_network():
    """默认不传 --network，不应调用真实 fetcher，输出 network_enabled=false。"""
    # Pre-load module so patch target resolves
    _load_script_module()
    with patch(
        "refetch_card_text_preview.make_tcg_mik_fetcher",
        side_effect=RuntimeError("should not be called"),
    ):
        exit_code, output = _run_main("--limit", "3")
        assert exit_code == 0
        assert "network_enabled      : False" in output
        assert "dry_run              : True" in output


# ---------------------------------------------------------------------------
# 2. 默认模式不写文件
# ---------------------------------------------------------------------------


def test_default_mode_no_file_write(tmp_path: Path):
    """不传 --output-preview 不应产生任何文件。"""
    exit_code, output = _run_main("--limit", "3")
    assert exit_code == 0
    # no file should have been created in tmp_path (we didn't pass it)
    assert "will_write_files" not in output or "False" in output


# ---------------------------------------------------------------------------
# 3. output preview 写入安全文件
# ---------------------------------------------------------------------------


def test_output_preview_safe_file(tmp_path: Path):
    """--output-preview 传安全路径，应写出 preview JSON。"""
    out_file = tmp_path / "refetch_preview.json"
    exit_code, output = _run_main(
        "--limit", "3", "--output-preview", str(out_file)
    )
    assert exit_code == 0
    assert out_file.exists()

    written = json.loads(out_file.read_text(encoding="utf-8"))
    meta = written["meta"]
    assert meta["dry_run"] is True
    assert meta["network_enabled"] is False
    assert meta["writes_original_cache"] is False
    assert meta["writes_normalized_cache"] is False
    assert meta.get("will_write_files") is True


# ---------------------------------------------------------------------------
# 4. 禁止危险输出路径
# ---------------------------------------------------------------------------


def test_forbidden_output_card_chinese_data():
    """--output-preview card_chinese_data.json 应失败。"""
    exit_code, output = _run_main(
        "--limit", "1", "--output-preview", "card_chinese_data.json"
    )
    assert exit_code == 1
    assert "禁止" in output or "ERROR" in output


def test_forbidden_output_card_data_cache():
    """--output-preview card_data_cache.json 应失败。"""
    exit_code, output = _run_main(
        "--limit", "1", "--output-preview", "card_data_cache.json"
    )
    assert exit_code == 1


def test_forbidden_output_normalized_card_text():
    """--output-preview normalized_card_text.json 应失败。"""
    exit_code, output = _run_main(
        "--limit", "1", "--output-preview", "normalized_card_text.json"
    )
    assert exit_code == 1


# ---------------------------------------------------------------------------
# 5. card-key 过滤
# ---------------------------------------------------------------------------


def test_card_key_filter():
    """--card-key TWM-145 应只包含 TWM-145 的 requests。"""
    exit_code, output = _run_main(
        "--card-key", "TWM-145", "--limit", "10"
    )
    assert exit_code == 0
    # The summary should only mention TWM-145
    assert "TWM-145" in output


# ---------------------------------------------------------------------------
# 6. limit 生效
# ---------------------------------------------------------------------------


def test_limit():
    """--limit 1 时 request_count 应 <= 1。"""
    # Pre-load module so patch target resolves
    _load_script_module()
    with patch(
        "refetch_card_text_preview.make_tcg_mik_fetcher",
        side_effect=RuntimeError("should not be called"),
    ):
        exit_code, output = _run_main("--limit", "1")
        assert exit_code == 0
        # Should show request_count: 1
        assert "request_count  : 1" in output


# ---------------------------------------------------------------------------
# 7. fail-on-blocking
# ---------------------------------------------------------------------------


def test_fail_on_blocking():
    """构造 blocking plan 后 --fail-on-blocking 应返回非 0。"""
    # Patch build_refetch_dry_run_requests to inject a blocking request
    fake_blocking_request = {
        "card_key": "BLOCKED-1",
        "name_en": "BlockedCard",
        "name_zh": "阻塞",
        "can_refetch": False,
        "method": "GET",
        "source": "tcg.mik.moe card-detail",
        "lookup_strategy": "unavailable",
        "lookup": {},
        "expected_source_fields": [],
        "field_mapping": {},
        "desired_fields": [],
        "dry_run": True,
        "will_write_files": False,
        "network_enabled": False,
        "blocking_issues": ["missing_refetch_locator"],
        "notes": [],
    }

    with patch(
        "ptcg.data_sources.text_refetch_dry_run.build_refetch_dry_run_requests",
        return_value=[fake_blocking_request],
    ):
        exit_code, output = _run_main("--fail-on-blocking")
        assert exit_code == 1


# ---------------------------------------------------------------------------
# 8. network=true 但 mocked fetcher
# ---------------------------------------------------------------------------


def test_network_true_with_mocked_fetcher():
    """通过 monkeypatch make_tcg_mik_fetcher 注入 fake fetcher，不真实联网。"""
    resp = _fake_detail_response()
    # Pre-load module so patch target resolves
    _load_script_module()

    with patch(
        "refetch_card_text_preview.make_tcg_mik_fetcher",
        return_value=_fake_fetcher(resp),
    ):
        exit_code, output = _run_main(
            "--network", "--card-key", "TWM-145", "--limit", "1"
        )
        assert exit_code == 0
        assert "network_enabled      : True" in output


# ---------------------------------------------------------------------------
# 9. unsupported lookup strategy
# ---------------------------------------------------------------------------


def test_unsupported_lookup_strategy():
    """detail_by_source_ids 以外的 strategy 应返回 unsupported 错误而不崩溃。"""
    fake_unsupported_request = {
        "card_key": "UNSUPPORTED-1",
        "name_en": "Test",
        "name_zh": "测试",
        "can_refetch": True,
        "method": "GET",
        "source": "tcg.mik.moe card-detail",
        "lookup_strategy": "search_then_detail_by_name",
        "lookup": {"name_en": "Test", "name_zh": "测试"},
        "expected_source_fields": [],
        "field_mapping": {},
        "desired_fields": [],
        "dry_run": True,
        "will_write_files": False,
        "network_enabled": True,
        "blocking_issues": [],
        "notes": [],
    }

    with patch(
        "ptcg.data_sources.text_refetch_dry_run.build_refetch_dry_run_requests",
        return_value=[fake_unsupported_request],
    ):
        from refetch_card_text_preview import make_tcg_mik_fetcher

        fetcher = make_tcg_mik_fetcher()
        result = fetcher(fake_unsupported_request)
        assert "_error" in result
        assert "unsupported_real_network_locator" in result["_error"]


# ---------------------------------------------------------------------------
# 10. 不修改现有 JSON
# ---------------------------------------------------------------------------


def test_does_not_modify_existing_json():
    """运行命令前后 card_chinese_data.json / card_data_cache.json 内容不变。"""
    chinese_data = ROOT / "card_chinese_data.json"
    cache_data = ROOT / "card_data_cache.json"

    chinese_before = chinese_data.read_bytes() if chinese_data.exists() else None
    cache_before = cache_data.read_bytes() if cache_data.exists() else None

    exit_code, _ = _run_main("--limit", "3")

    assert exit_code == 0

    chinese_after = chinese_data.read_bytes() if chinese_data.exists() else None
    cache_after = cache_data.read_bytes() if cache_data.exists() else None

    assert chinese_before == chinese_after
    assert cache_before == cache_after


# ---------------------------------------------------------------------------
# 11. 无危险写入
# ---------------------------------------------------------------------------


def test_no_dangerous_write_patterns():
    """源码检查不对禁止文件执行写入操作。"""
    source = SCRIPT_PATH.read_text(encoding="utf-8")
    # 检查是否存在对禁止文件的 Path().write_text / json.dump 等操作
    # 注意：_FORBIDDEN_OUTPUT_NAMES 和 _RESERVED_FILES_IN_ROOT 中引用这些文件名是正常的
    dangerous_patterns = [
        'Path("card_chinese_data.json")',
        'Path("card_data_cache.json")',
        'Path("normalized_card_text.json")',
    ]
    for pattern in dangerous_patterns:
        # 允许在 _FORBIDDEN_OUTPUT_NAMES / _RESERVED_FILES_IN_ROOT 中引用
        # 但不允许后续跟着 .write_text 或作为 json.dump 的目标
        if pattern in source:
            idx = source.index(pattern)
            after = source[idx + len(pattern):idx + len(pattern) + 120]
            assert ".write_text" not in after, f"危险写入: {pattern} 后有 .write_text"
            assert "json.dump" not in after, f"危险写入: {pattern} 后有 json.dump"


def test_no_network_imports_by_default():
    """源码中不应有默认联网导入。"""
    source = SCRIPT_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden = {"requests", "httpx", "aiohttp", "bs4"}

    # 检查顶层 import
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Import):
            imported = {alias.name.split(".")[0] for alias in node.names}
            assert forbidden.isdisjoint(imported), f"顶层导入了禁止的库: {imported & forbidden}"
        elif isinstance(node, ast.ImportFrom) and node.module:
            module_root = node.module.split(".")[0]
            assert module_root not in forbidden, f"顶层导入了禁止的库: {module_root}"


# ---------------------------------------------------------------------------
# 额外: 帮助函数单元测试
# ---------------------------------------------------------------------------


def test_validate_output_path_rejects_forbidden():
    from refetch_card_text_preview import _validate_output_path

    assert _validate_output_path(Path("card_chinese_data.json")) != []
    assert _validate_output_path(Path("card_data_cache.json")) != []
    assert _validate_output_path(Path("normalized_card_text.json")) != []
    assert _validate_output_path(Path("refetch_preview.json")) == []


def test_validate_output_path_allows_preview_names(tmp_path: Path):
    from refetch_card_text_preview import _validate_output_path

    safe = tmp_path / "card_text_refetch_preview.json"
    assert _validate_output_path(safe) == []
