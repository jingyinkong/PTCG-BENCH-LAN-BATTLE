"""测试 semantic extraction input preview 构建。

覆盖：
1. 从 application preview 生成 input package
2. 只选择 prompt_ready=true 且 applied=true
3. --card-key 过滤
4. --limit 生效
5. dangerous output path rejected
6. 不生成 semantic ops JSON
7. 不生成 prompt
8. op inventory 包含当前支持 ops
9. no network / no LLM imports
10. original JSON unchanged
11. fail-on-not-ready
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "build_semantic_extraction_input.py"

CHINESE_DATA = ROOT / "card_chinese_data.json"
CACHE_DATA = ROOT / "card_data_cache.json"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _load_script_module():
    spec = importlib.util.spec_from_file_location(
        "build_semantic_extraction_input", SCRIPT_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load script: {SCRIPT_PATH}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["build_semantic_extraction_input"] = mod
    spec.loader.exec_module(mod)
    return mod


def _run_main(*args: str) -> tuple[int, str]:
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


def _make_application_preview(
    applications: list[dict[str, Any]],
) -> dict[str, Any]:
    """构建符合 apply_refetch_preview.py 格式的 application preview JSON。"""
    return {
        "meta": {
            "dry_run": True,
            "network_enabled": False,
            "writes_original_cache": False,
            "writes_normalized_cache": False,
            "writes_formal_normalized_json": False,
            "schema_version": "normalized_patch_application_preview.v1",
        },
        "summary": {
            "input_result_count": len(applications),
            "processed_count": len(applications),
            "applied_count": len(applications),
            "skipped_count": 0,
            "error_count": 0,
            "warning_count": 0,
        },
        "applications": applications,
    }


def _ready_application(
    card_key: str,
    name_en: str = "",
    name_zh: str = "",
    set_code: str = "TWM",
    number: str = "145",
    local_file: str = "ptcg/cards/TWM/twm145carmine.py",
    rules_text: str = "测试效果文本",
    applied: bool = True,
    prompt_ready: bool = True,
) -> dict[str, Any]:
    """创建一个 prompt_ready 的 application entry fixture。"""
    return {
        "card_key": card_key,
        "dry_run": True,
        "applied": applied,
        "updated_record_preview": {
            "card_key": card_key,
            "identity": {
                "card_key": card_key,
                "name_en": name_en,
                "name_zh": name_zh,
                "set_code": set_code,
                "set_name": set_code,
                "number": number,
                "normalized_number": number,
                "local_file": local_file,
                "local_class_name": f"{set_code}{number}Card",
            },
            "classification": {
                "card_supertype": "Trainer",
                "trainer_subtype": "Supporter",
                "classification_source": "local_class",
                "classification_confidence": "high",
            },
            "text": {
                "rules_text_zh": rules_text,
                "trainer_text_zh": rules_text,
                "full_text_zh": rules_text,
                "text_available": True,
                "text_quality": "refetched",
            },
            "quality_flags": {
                "missing_rules_text": False,
                "untrusted_card_type": False,
                "needs_text_refetch": False,
                "prompt_ready": prompt_ready,
            },
            "provenance": {
                "sources": [
                    {"id": "card_chinese_data", "type": "json"},
                    {"id": "card_data_cache", "type": "json"},
                    {"id": "local_class", "type": "python"},
                    {
                        "id": "tcg.mik.card-detail",
                        "type": "refetch",
                        "applied_fields": ["text.rules_text_zh"],
                    },
                ],
                "field_source_map": {
                    "text.rules_text_zh": "tcg.mik.card-detail.description",
                    "text.full_text_zh": "tcg.mik.card-detail.description",
                    "classification.card_supertype": "tcg.mik.card-detail.cardType",
                },
                "refetch": {
                    "source": "tcg.mik.moe card-detail",
                    "response_shape": "flat",
                },
            },
        },
        "application_report": {
            "applied_fields": ["text.rules_text_zh", "text.full_text_zh"],
            "skipped_fields": [],
            "warnings": [],
            "errors": [],
            "quality_flag_updates": {"prompt_ready": "False→True"},
            "provenance_updates": {
                "field_source_map_keys": ["text.rules_text_zh"],
                "sources_added": "tcg.mik.card-detail",
            },
        },
    }


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# 1. 成功从 application preview 生成 input package
# ---------------------------------------------------------------------------


def test_success_generate_input_package(tmp_path: Path):
    """5 张 A 类卡全部进入 input package。"""
    app_preview_path = tmp_path / "app_preview.json"
    preview = _make_application_preview([
        _ready_application("TWM-145", name_zh="丹瑜"),
        _ready_application("SSH-178", name_zh="博士的研究"),
        _ready_application("PAL-185", name_zh="奇树"),
        _ready_application("FLI-108", name_zh="测试卡F"),
        _ready_application("ASR-150", name_zh="杜娟"),
    ])
    app_preview_path.write_text(
        json.dumps(preview, ensure_ascii=False), encoding="utf-8"
    )

    output_path = tmp_path / "input_preview.json"

    exit_code, output = _run_main(
        "--input-application-preview", str(app_preview_path),
        "--limit", "10",
        "--output-input-preview", str(output_path),
    )
    assert exit_code == 0

    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert data["meta"]["calls_llm"] is False
    assert data["meta"]["writes_semantic_ops_json"] is False
    assert data["meta"]["writes_prompt"] is False
    assert data["summary"]["selected_count"] == 5
    assert data["summary"]["not_ready_count"] == 0
    assert len(data["cards"]) == 5

    # 每张卡包含必要字段
    for card in data["cards"]:
        assert "card_key" in card
        assert "identity" in card
        assert "classification" in card
        assert "normalized_text" in card
        assert "quality_flags" in card
        assert "provenance_summary" in card
        assert "application_summary" in card
        assert "semantic_extraction_task" in card
        assert "known_runtime_support" in card
        assert card["semantic_extraction_task"]["must_not_emit_final_json"] is True
        assert card["semantic_extraction_task"]["must_preserve_legacy_behavior"] is True

    # 验证 card_key 顺序
    card_keys = [c["card_key"] for c in data["cards"]]
    assert "TWM-145" in card_keys
    assert "SSH-178" in card_keys
    assert "PAL-185" in card_keys
    assert "FLI-108" in card_keys
    assert "ASR-150" in card_keys

    # stdout
    assert "语义提取输入包 preview 完成" in output


# ---------------------------------------------------------------------------
# 2. 只选择 prompt_ready=true 且 applied=true
# ---------------------------------------------------------------------------


def test_filter_not_ready(tmp_path: Path):
    """mixed input：有 applied=false、有 prompt_ready=false，默认跳过。"""
    app_preview_path = tmp_path / "app_preview.json"
    preview = _make_application_preview([
        _ready_application("TWM-145", applied=True, prompt_ready=True),
        _ready_application("SSH-178", applied=False, prompt_ready=True),
        _ready_application("PAL-185", applied=True, prompt_ready=False),
    ])
    app_preview_path.write_text(
        json.dumps(preview, ensure_ascii=False), encoding="utf-8"
    )

    output_path = tmp_path / "input_preview.json"

    exit_code, output = _run_main(
        "--input-application-preview", str(app_preview_path),
        "--output-input-preview", str(output_path),
    )
    assert exit_code == 0

    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert data["summary"]["selected_count"] == 1
    assert data["summary"]["ready_count"] == 1
    assert data["summary"]["not_ready_count"] == 2
    assert len(data["cards"]) == 1
    assert data["cards"][0]["card_key"] == "TWM-145"


# ---------------------------------------------------------------------------
# 3. --card-key 过滤
# ---------------------------------------------------------------------------


def test_card_key_filter(tmp_path: Path):
    """--card-key 只输出指定卡。"""
    app_preview_path = tmp_path / "app_preview.json"
    preview = _make_application_preview([
        _ready_application("TWM-145"),
        _ready_application("SSH-178"),
        _ready_application("PAL-185"),
    ])
    app_preview_path.write_text(
        json.dumps(preview, ensure_ascii=False), encoding="utf-8"
    )

    output_path = tmp_path / "input_preview.json"

    exit_code, output = _run_main(
        "--input-application-preview", str(app_preview_path),
        "--card-key", "TWM-145",
        "--card-key", "SSH-178",
        "--output-input-preview", str(output_path),
    )
    assert exit_code == 0

    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert data["summary"]["selected_count"] == 2
    card_keys = [c["card_key"] for c in data["cards"]]
    assert "TWM-145" in card_keys
    assert "SSH-178" in card_keys
    assert "PAL-185" not in card_keys


# ---------------------------------------------------------------------------
# 4. --limit 生效
# ---------------------------------------------------------------------------


def test_limit(tmp_path: Path):
    """--limit 限制处理条数。"""
    app_preview_path = tmp_path / "app_preview.json"
    preview = _make_application_preview([
        _ready_application("TWM-145"),
        _ready_application("SSH-178"),
        _ready_application("PAL-185"),
        _ready_application("FLI-108"),
        _ready_application("ASR-150"),
    ])
    app_preview_path.write_text(
        json.dumps(preview, ensure_ascii=False), encoding="utf-8"
    )

    output_path = tmp_path / "input_preview.json"

    exit_code, output = _run_main(
        "--input-application-preview", str(app_preview_path),
        "--limit", "2",
        "--output-input-preview", str(output_path),
    )
    assert exit_code == 0

    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert data["summary"]["selected_count"] == 2
    assert len(data["cards"]) == 2


# ---------------------------------------------------------------------------
# 5. dangerous output path rejected — card_chinese_data.json
# ---------------------------------------------------------------------------


def test_dangerous_output_path_card_chinese(tmp_path: Path):
    """禁止 --output-input-preview card_chinese_data.json。"""
    app_preview_path = tmp_path / "app_preview.json"
    preview = _make_application_preview([_ready_application("TWM-145")])
    app_preview_path.write_text(
        json.dumps(preview, ensure_ascii=False), encoding="utf-8"
    )

    exit_code, output = _run_main(
        "--input-application-preview", str(app_preview_path),
        "--output-input-preview", "card_chinese_data.json",
    )
    assert exit_code != 0
    assert "禁止" in output


def test_dangerous_output_path_card_data_cache(tmp_path: Path):
    """禁止 --output-input-preview card_data_cache.json。"""
    app_preview_path = tmp_path / "app_preview.json"
    preview = _make_application_preview([_ready_application("TWM-145")])
    app_preview_path.write_text(
        json.dumps(preview, ensure_ascii=False), encoding="utf-8"
    )

    exit_code, output = _run_main(
        "--input-application-preview", str(app_preview_path),
        "--output-input-preview", "card_data_cache.json",
    )
    assert exit_code != 0
    assert "禁止" in output


def test_dangerous_output_path_normalized_card_text(tmp_path: Path):
    """禁止 --output-input-preview data/normalized_card_text.json。"""
    app_preview_path = tmp_path / "app_preview.json"
    preview = _make_application_preview([_ready_application("TWM-145")])
    app_preview_path.write_text(
        json.dumps(preview, ensure_ascii=False), encoding="utf-8"
    )

    exit_code, output = _run_main(
        "--input-application-preview", str(app_preview_path),
        "--output-input-preview", "data/normalized_card_text.json",
    )
    assert exit_code != 0
    assert "禁止" in output


def test_dangerous_output_path_semantic_ops_json(tmp_path: Path):
    """禁止 --output-input-preview semantic_ops.json。"""
    app_preview_path = tmp_path / "app_preview.json"
    preview = _make_application_preview([_ready_application("TWM-145")])
    app_preview_path.write_text(
        json.dumps(preview, ensure_ascii=False), encoding="utf-8"
    )

    exit_code, output = _run_main(
        "--input-application-preview", str(app_preview_path),
        "--output-input-preview", "semantic_ops.json",
    )
    assert exit_code != 0
    assert "禁止" in output


def test_dangerous_output_path_prompt_md(tmp_path: Path):
    """禁止 --output-input-preview prompt.md。"""
    app_preview_path = tmp_path / "app_preview.json"
    preview = _make_application_preview([_ready_application("TWM-145")])
    app_preview_path.write_text(
        json.dumps(preview, ensure_ascii=False), encoding="utf-8"
    )

    exit_code, output = _run_main(
        "--input-application-preview", str(app_preview_path),
        "--output-input-preview", "prompt.md",
    )
    assert exit_code != 0
    assert "禁止" in output


# ---------------------------------------------------------------------------
# 6. 不生成 semantic ops JSON
# ---------------------------------------------------------------------------


def test_no_semantic_ops_json_generated(tmp_path: Path):
    """输出中不含 final semantic ops 字段。"""
    from ptcg.data_sources.semantic_extraction_input import (
        build_semantic_extraction_input_preview,
    )

    preview = _make_application_preview([_ready_application("TWM-145")])
    result = build_semantic_extraction_input_preview(preview)

    assert result["meta"]["writes_semantic_ops_json"] is False
    # output 中不应包含 semantic_ops 字段
    assert "semantic_ops" not in result
    for card in result.get("cards", []):
        assert "semantic_ops" not in card
        assert card["semantic_extraction_task"]["must_not_emit_final_json"] is True


# ---------------------------------------------------------------------------
# 7. 不生成 prompt
# ---------------------------------------------------------------------------


def test_no_prompt_generated(tmp_path: Path):
    """输出中不含 final prompt text。"""
    from ptcg.data_sources.semantic_extraction_input import (
        build_semantic_extraction_input_preview,
    )

    preview = _make_application_preview([_ready_application("TWM-145")])
    result = build_semantic_extraction_input_preview(preview)

    assert result["meta"]["writes_prompt"] is False
    assert "prompt" not in result
    for card in result.get("cards", []):
        assert "prompt" not in card


# ---------------------------------------------------------------------------
# 8. op inventory 包含当前支持 ops
# ---------------------------------------------------------------------------


def test_op_inventory_contains_supported_ops(tmp_path: Path):
    """op_inventory 包含当前支持的 move/discard/draw/mark ops。"""
    app_preview_path = tmp_path / "app_preview.json"
    preview = _make_application_preview([_ready_application("TWM-145")])
    app_preview_path.write_text(
        json.dumps(preview, ensure_ascii=False), encoding="utf-8"
    )

    output_path = tmp_path / "input_preview.json"

    exit_code, output = _run_main(
        "--input-application-preview", str(app_preview_path),
        "--output-input-preview", str(output_path),
    )
    assert exit_code == 0

    data = json.loads(output_path.read_text(encoding="utf-8"))
    allowed = data["op_inventory"]["allowed_ops"]
    disallowed = data["op_inventory"]["disallowed_patterns"]

    assert "move_cards" in allowed
    assert "discard_cards" in allowed
    assert "draw_cards" in allowed
    assert "mark_supporter_played" in allowed
    assert "choice" in disallowed or any("choice" in d for d in disallowed)

    # 每张卡也有 known_runtime_support
    for card in data["cards"]:
        card_ops = card["known_runtime_support"]["available_ops"]
        assert "move_cards" in card_ops
        assert "discard_cards" in card_ops
        assert "draw_cards" in card_ops
        assert "mark_supporter_played" in card_ops


# ---------------------------------------------------------------------------
# 9. no network / no LLM imports
# ---------------------------------------------------------------------------


def test_no_network_imports():
    """核心模块和 CLI 不 import 网络库。"""
    core_path = ROOT / "ptcg" / "data_sources" / "semantic_extraction_input.py"
    core_source = core_path.read_text(encoding="utf-8")

    forbidden_imports = [
        "import requests",
        "import httpx",
        "import aiohttp",
        "import openai",
        "import anthropic",
    ]

    for forbidden in forbidden_imports:
        assert forbidden not in core_source, f"核心模块不应导入 {forbidden}"

    cli_source = SCRIPT_PATH.read_text(encoding="utf-8")
    for forbidden in forbidden_imports:
        assert forbidden not in cli_source, f"CLI 不应导入 {forbidden}"


# ---------------------------------------------------------------------------
# 10. original JSON unchanged
# ---------------------------------------------------------------------------


def test_original_json_unchanged(tmp_path: Path):
    """cart_chinese_data.json / card_data_cache.json 内容不变。"""
    sha_cn_before = _file_sha256(CHINESE_DATA)
    sha_cache_before = _file_sha256(CACHE_DATA)

    app_preview_path = tmp_path / "app_preview.json"
    preview = _make_application_preview([_ready_application("TWM-145")])
    app_preview_path.write_text(
        json.dumps(preview, ensure_ascii=False), encoding="utf-8"
    )

    output_path = tmp_path / "input_preview.json"
    exit_code, _ = _run_main(
        "--input-application-preview", str(app_preview_path),
        "--output-input-preview", str(output_path),
    )
    assert exit_code == 0

    sha_cn_after = _file_sha256(CHINESE_DATA)
    sha_cache_after = _file_sha256(CACHE_DATA)

    assert sha_cn_before == sha_cn_after, "card_chinese_data.json 不应被修改"
    assert sha_cache_before == sha_cache_after, "card_data_cache.json 不应被修改"


# ---------------------------------------------------------------------------
# 11. fail-on-not-ready
# ---------------------------------------------------------------------------


def test_fail_on_not_ready_exit_non_zero(tmp_path: Path):
    """--fail-on-not-ready 时若存在 not_ready 的卡，exit code 非 0。"""
    app_preview_path = tmp_path / "app_preview.json"
    preview = _make_application_preview([
        _ready_application("TWM-145", applied=True, prompt_ready=True),
        _ready_application("SSH-178", applied=False, prompt_ready=True),
    ])
    app_preview_path.write_text(
        json.dumps(preview, ensure_ascii=False), encoding="utf-8"
    )

    exit_code, output = _run_main(
        "--input-application-preview", str(app_preview_path),
        "--fail-on-not-ready",
    )
    assert exit_code != 0

    # 不带 --fail-on-not-ready 应该 exit 0
    exit_code2, _ = _run_main(
        "--input-application-preview", str(app_preview_path),
    )
    assert exit_code2 == 0


def test_fail_on_not_ready_no_write_on_dangerous(tmp_path: Path):
    """--fail-on-not-ready 时不写危险文件。"""
    app_preview_path = tmp_path / "app_preview.json"
    preview = _make_application_preview([
        _ready_application("TWM-145", applied=True, prompt_ready=True),
        _ready_application("SSH-178", applied=False, prompt_ready=True),
    ])
    app_preview_path.write_text(
        json.dumps(preview, ensure_ascii=False), encoding="utf-8"
    )

    exit_code, output = _run_main(
        "--input-application-preview", str(app_preview_path),
        "--fail-on-not-ready",
        "--output-input-preview", "card_chinese_data.json",
    )
    assert exit_code != 0
    assert "禁止" in output


# ---------------------------------------------------------------------------
# 12. 默认 stdout 模式不写文件
# ---------------------------------------------------------------------------


def test_default_stdout_no_file_write(tmp_path: Path):
    """不传 --output-input-preview 不应产生任何文件。"""
    app_preview_path = tmp_path / "app_preview.json"
    preview = _make_application_preview([_ready_application("TWM-145")])
    app_preview_path.write_text(
        json.dumps(preview, ensure_ascii=False), encoding="utf-8"
    )

    exit_code, output = _run_main(
        "--input-application-preview", str(app_preview_path),
    )
    assert exit_code == 0
    assert "语义提取输入包 preview 完成" in output
    assert "calls_llm" in output
