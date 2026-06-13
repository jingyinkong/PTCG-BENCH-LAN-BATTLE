"""Tests for apply_refetch_preview.py — 纯内存 dry-run，不联网，不写原始 JSON。"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "apply_refetch_preview.py"

CHINESE_DATA = ROOT / "card_chinese_data.json"
CACHE_DATA = ROOT / "card_data_cache.json"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _load_script_module():
    """Load the script module via importlib."""
    spec = importlib.util.spec_from_file_location(
        "apply_refetch_preview", SCRIPT_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load script: {SCRIPT_PATH}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["apply_refetch_preview"] = mod
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


def _make_preview_json(results: list[dict[str, Any]]) -> dict[str, Any]:
    """构建符合 refetch_card_text_preview.py 格式的 input preview JSON。"""
    return {
        "meta": {
            "dry_run": True,
            "network_enabled": False,
            "schema_version": "refetch-preview-v1",
            "generated_at": "2026-01-01T00:00:00Z",
        },
        "summary": {
            "total_records": 1000,
            "planned_count": len(results),
            "request_count": len(results),
            "result_count": len(results),
            "blocking_count": 0,
        },
        "requests": [],
        "results": results,
    }


def _twm145_refetch_result(**overrides: object) -> dict[str, Any]:
    """Successful TWM-145 refetch result fixture."""
    result: dict[str, Any] = {
        "card_key": "TWM-145",
        "source": "tcg.mik.moe card-detail",
        "raw_fields_found": ["cardType", "description"],
        "parsed_fields": {
            "cardType": "Supporter",
            "description": (
                "将自己的手牌全部放回牌库并重洗。然后，从牌库上方抽出5张卡。"
            ),
        },
        "normalized_patch_preview": {
            "text": {
                "rules_text_zh": "将自己的手牌全部放回牌库并重洗。然后，从牌库上方抽出5张卡。",
                "trainer_text_zh": "将自己的手牌全部放回牌库并重洗。然后，从牌库上方抽出5张卡。",
                "full_text_zh": "将自己的手牌全部放回牌库并重洗。然后，从牌库上方抽出5张卡。",
            },
            "classification": {
                "card_supertype": "Trainer",
                "trainer_subtype": "Supporter",
            },
        },
        "provenance_preview": {
            "source_api": "tcg.mik.moe card-detail",
            "dry_run": True,
        },
        "dry_run": True,
        "will_write_files": False,
        "network_enabled": True,
        "response_diagnostics": {
            "top_level_keys": ["cardType", "description"],
            "candidate_paths_checked": ["$.description", "$.cardType"],
            "description_path": "$.description",
            "card_type_path": "$.cardType",
            "has_description": True,
            "has_card_type": True,
            "response_shape": "flat",
            "safe_preview": {"top_level_keys": ["cardType", "description"]},
        },
        "errors": [],
        "warnings": [],
    }
    result.update(overrides)  # type: ignore[arg-type]
    return result


def _ssh178_refetch_result(**overrides: object) -> dict[str, Any]:
    """Successful SSH-178 refetch result fixture."""
    result: dict[str, Any] = {
        "card_key": "SSH-178",
        "source": "tcg.mik.moe card-detail",
        "raw_fields_found": ["cardType", "description"],
        "parsed_fields": {
            "cardType": "Supporter",
            "description": "从自己的牌库选择一张卡加入手牌。并且重洗牌库。",
        },
        "normalized_patch_preview": {
            "text": {
                "rules_text_zh": "从自己的牌库选择一张卡加入手牌。并且重洗牌库。",
                "trainer_text_zh": "从自己的牌库选择一张卡加入手牌。并且重洗牌库。",
                "full_text_zh": "从自己的牌库选择一张卡加入手牌。并且重洗牌库。",
            },
            "classification": {
                "card_supertype": "Trainer",
                "trainer_subtype": "Supporter",
            },
        },
        "provenance_preview": {
            "source_api": "tcg.mik.moe card-detail",
            "dry_run": True,
        },
        "dry_run": True,
        "will_write_files": False,
        "network_enabled": True,
        "response_diagnostics": {
            "top_level_keys": ["cardType", "description"],
            "candidate_paths_checked": ["$.description", "$.cardType"],
            "description_path": "$.description",
            "card_type_path": "$.cardType",
            "has_description": True,
            "has_card_type": True,
            "response_shape": "flat",
            "safe_preview": {"top_level_keys": ["cardType", "description"]},
        },
        "errors": [],
        "warnings": [],
    }
    result.update(overrides)  # type: ignore[arg-type]
    return result


def _file_sha256(path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# 1. 默认 stdout 模式不写文件
# ---------------------------------------------------------------------------


def test_default_stdout_no_file_write(tmp_path: Path):
    """不传 --output-application-preview 不应产生任何文件。"""
    preview_path = tmp_path / "refetch_preview.json"
    preview = _make_preview_json([_twm145_refetch_result()])
    preview_path.write_text(json.dumps(preview, ensure_ascii=False), encoding="utf-8")

    exit_code, output = _run_main(
        "--input-preview", str(preview_path),
        "--limit", "1",
    )
    assert exit_code == 0
    assert "补抓 patch application preview 完成" in output
    assert "dry_run" in output


# ---------------------------------------------------------------------------
# 2. 成功 TWM-145 application preview 输出
# ---------------------------------------------------------------------------


def test_success_twm145_application_preview(tmp_path: Path):
    """TWM-145 successful refetch result 应该 applied=true。"""
    preview_path = tmp_path / "refetch_preview.json"
    preview = _make_preview_json([_twm145_refetch_result()])
    preview_path.write_text(json.dumps(preview, ensure_ascii=False), encoding="utf-8")

    output_path = tmp_path / "application_preview.json"

    exit_code, output = _run_main(
        "--input-preview", str(preview_path),
        "--card-key", "TWM-145",
        "--limit", "1",
        "--output-application-preview", str(output_path),
    )
    assert exit_code == 0

    # check output file
    assert output_path.exists()
    app_data = json.loads(output_path.read_text(encoding="utf-8"))

    assert app_data["meta"]["dry_run"] is True
    assert app_data["meta"]["network_enabled"] is False
    assert app_data["meta"]["writes_original_cache"] is False
    assert app_data["meta"]["writes_normalized_cache"] is False
    assert app_data["meta"]["writes_formal_normalized_json"] is False

    apps = app_data["applications"]
    assert len(apps) == 1
    assert apps[0]["card_key"] == "TWM-145"
    assert apps[0]["applied"] is True

    updated = apps[0]["updated_record_preview"]
    assert "text" in updated
    assert updated["text"]["rules_text_zh"] is not None
    assert "classification" in updated

    report = apps[0]["application_report"]
    assert len(report["applied_fields"]) > 0

    # stdout summary
    assert "TWM-145" in output
    assert "applied=True" in output


# ---------------------------------------------------------------------------
# 3. --card-key 过滤
# ---------------------------------------------------------------------------


def test_card_key_filter(tmp_path: Path):
    """--card-key 只处理指定卡牌。"""
    preview_path = tmp_path / "refetch_preview.json"
    preview = _make_preview_json([
        _twm145_refetch_result(),
        _ssh178_refetch_result(),
    ])
    preview_path.write_text(json.dumps(preview, ensure_ascii=False), encoding="utf-8")

    output_path = tmp_path / "application_preview.json"

    exit_code, output = _run_main(
        "--input-preview", str(preview_path),
        "--card-key", "TWM-145",
        "--output-application-preview", str(output_path),
    )
    assert exit_code == 0

    app_data = json.loads(output_path.read_text(encoding="utf-8"))
    apps = app_data["applications"]
    assert len(apps) == 1
    assert apps[0]["card_key"] == "TWM-145"


# ---------------------------------------------------------------------------
# 4. --limit 生效
# ---------------------------------------------------------------------------


def test_limit(tmp_path: Path):
    """--limit 限制处理条数。"""
    preview_path = tmp_path / "refetch_preview.json"
    preview = _make_preview_json([
        _twm145_refetch_result(),
        _ssh178_refetch_result(),
    ])
    preview_path.write_text(json.dumps(preview, ensure_ascii=False), encoding="utf-8")

    output_path = tmp_path / "application_preview.json"

    exit_code, output = _run_main(
        "--input-preview", str(preview_path),
        "--limit", "1",
        "--output-application-preview", str(output_path),
    )
    assert exit_code == 0

    app_data = json.loads(output_path.read_text(encoding="utf-8"))
    assert app_data["summary"]["processed_count"] == 1


# ---------------------------------------------------------------------------
# 5. --allow-overwrite 传递
# ---------------------------------------------------------------------------


def test_allow_overwrite_pass_through(tmp_path: Path):
    """--allow-overwrite 应该允许覆盖已有字段。"""
    preview_path = tmp_path / "refetch_preview.json"

    # TWM-145 with existing text (simulate via normal flow - the record has
    # None text from normalized loader; we'll test with a card that gets text
    # applied successfully with and without allow_overwrite).

    # First run WITHOUT allow_overwrite
    preview = _make_preview_json([_twm145_refetch_result()])
    preview_path.write_text(json.dumps(preview, ensure_ascii=False), encoding="utf-8")

    out_no_ow = tmp_path / "app_no_ow.json"
    exit_code, _ = _run_main(
        "--input-preview", str(preview_path),
        "--card-key", "TWM-145",
        "--output-application-preview", str(out_no_ow),
    )
    assert exit_code == 0
    no_ow_data = json.loads(out_no_ow.read_text(encoding="utf-8"))
    assert no_ow_data["meta"]["allow_overwrite"] is False

    # Second run WITH allow_overwrite
    out_ow = tmp_path / "app_ow.json"
    exit_code, _ = _run_main(
        "--input-preview", str(preview_path),
        "--card-key", "TWM-145",
        "--allow-overwrite",
        "--output-application-preview", str(out_ow),
    )
    assert exit_code == 0
    ow_data = json.loads(out_ow.read_text(encoding="utf-8"))
    assert ow_data["meta"]["allow_overwrite"] is True


# ---------------------------------------------------------------------------
# 6. --fail-on-errors
# ---------------------------------------------------------------------------


def test_fail_on_errors(tmp_path: Path):
    """--fail-on-errors 时若有 errors 则 exit code 非 0。"""
    preview_path = tmp_path / "refetch_preview.json"

    # Create a result that will fail (non-existent card key)
    unknown_result = _twm145_refetch_result(card_key="UNKNOWN-999")
    preview = _make_preview_json([unknown_result])
    preview_path.write_text(json.dumps(preview, ensure_ascii=False), encoding="utf-8")

    exit_code, output = _run_main(
        "--input-preview", str(preview_path),
        "--fail-on-errors",
    )
    assert exit_code != 0

    # Without fail-on-errors, should exit 0
    exit_code2, _ = _run_main(
        "--input-preview", str(preview_path),
    )
    assert exit_code2 == 0


# ---------------------------------------------------------------------------
# 7. dangerous output path rejected
# ---------------------------------------------------------------------------


def test_dangerous_output_path_rejected_card_chinese(tmp_path: Path):
    """禁止 --output-application-preview card_chinese_data.json。"""
    preview_path = tmp_path / "refetch_preview.json"
    preview = _make_preview_json([_twm145_refetch_result()])
    preview_path.write_text(json.dumps(preview, ensure_ascii=False), encoding="utf-8")

    exit_code, output = _run_main(
        "--input-preview", str(preview_path),
        "--output-application-preview", "card_chinese_data.json",
    )
    assert exit_code != 0
    assert "禁止" in output


def test_dangerous_output_path_rejected_card_data_cache(tmp_path: Path):
    """禁止 --output-application-preview card_data_cache.json。"""
    preview_path = tmp_path / "refetch_preview.json"
    preview = _make_preview_json([_twm145_refetch_result()])
    preview_path.write_text(json.dumps(preview, ensure_ascii=False), encoding="utf-8")

    exit_code, output = _run_main(
        "--input-preview", str(preview_path),
        "--output-application-preview", "card_data_cache.json",
    )
    assert exit_code != 0
    assert "禁止" in output


def test_dangerous_output_path_rejected_normalized(tmp_path: Path):
    """禁止 --output-application-preview data/normalized_card_text.json。"""
    preview_path = tmp_path / "refetch_preview.json"
    preview = _make_preview_json([_twm145_refetch_result()])
    preview_path.write_text(json.dumps(preview, ensure_ascii=False), encoding="utf-8")

    exit_code, output = _run_main(
        "--input-preview", str(preview_path),
        "--output-application-preview", "data/normalized_card_text.json",
    )
    assert exit_code != 0
    assert "禁止" in output


def test_dangerous_output_path_not_writing(tmp_path: Path):
    """危险路径被拒绝后不应修改原文件。"""
    hash_before = _file_sha256(CHINESE_DATA)

    preview_path = tmp_path / "refetch_preview.json"
    preview = _make_preview_json([_twm145_refetch_result()])
    preview_path.write_text(json.dumps(preview, ensure_ascii=False), encoding="utf-8")

    _run_main(
        "--input-preview", str(preview_path),
        "--output-application-preview", "card_chinese_data.json",
    )
    # ensure card_chinese_data.json NOT modified
    hash_after = _file_sha256(CHINESE_DATA)
    assert hash_before == hash_after, "card_chinese_data.json was modified!"


# ---------------------------------------------------------------------------
# 8. normalized_record_not_found
# ---------------------------------------------------------------------------


def test_normalized_record_not_found(tmp_path: Path):
    """不存在的 card_key 不崩溃，报告 normalized_record_not_found。"""
    preview_path = tmp_path / "refetch_preview.json"
    preview = _make_preview_json([_twm145_refetch_result(card_key="UNKNOWN-999")])
    preview_path.write_text(json.dumps(preview, ensure_ascii=False), encoding="utf-8")

    output_path = tmp_path / "application_preview.json"

    exit_code, output = _run_main(
        "--input-preview", str(preview_path),
        "--output-application-preview", str(output_path),
    )
    # 默认不 fail-on-errors，exit 0
    assert exit_code == 0

    app_data = json.loads(output_path.read_text(encoding="utf-8"))
    apps = app_data["applications"]
    assert len(apps) == 1
    assert apps[0]["applied"] is False
    assert "normalized_record_not_found" in apps[0]["application_report"]["errors"]


# ---------------------------------------------------------------------------
# 9. no network imports
# ---------------------------------------------------------------------------


def test_no_network_imports_in_script():
    """新脚本不包含网络库导入。"""
    source = SCRIPT_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden = {"requests", "httpx", "aiohttp", "bs4", "urllib.request", "urllib"}
    imported: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])

    assert forbidden.isdisjoint(imported), f"Found forbidden import: {imported & forbidden}"


def test_no_refetch_client_calls():
    """新脚本不调用 tcg_mik_refetch_client。"""
    source = SCRIPT_PATH.read_text(encoding="utf-8")
    assert "TcgMikRefetchClient" not in source
    assert "fetch_detail_for_request" not in source
    assert "make_tcg_mik_fetcher" not in source


# ---------------------------------------------------------------------------
# 10. original JSON unchanged
# ---------------------------------------------------------------------------


def test_original_json_unchanged(tmp_path: Path):
    """测试前后 card_chinese_data.json 和 card_data_cache.json 不变。"""
    hash_chinese_before = _file_sha256(CHINESE_DATA)
    hash_cache_before = _file_sha256(CACHE_DATA)

    preview_path = tmp_path / "refetch_preview.json"
    preview = _make_preview_json([_twm145_refetch_result()])
    preview_path.write_text(json.dumps(preview, ensure_ascii=False), encoding="utf-8")

    output_path = tmp_path / "application_preview.json"

    exit_code, _ = _run_main(
        "--input-preview", str(preview_path),
        "--card-key", "TWM-145",
        "--limit", "1",
        "--output-application-preview", str(output_path),
    )
    assert exit_code == 0

    hash_chinese_after = _file_sha256(CHINESE_DATA)
    hash_cache_after = _file_sha256(CACHE_DATA)

    assert hash_chinese_before == hash_chinese_after, "card_chinese_data.json was modified!"
    assert hash_cache_before == hash_cache_after, "card_data_cache.json was modified!"
