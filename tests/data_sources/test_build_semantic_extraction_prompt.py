"""测试 semantic extraction prompt preview。

覆盖：
1. SSH-178 成功生成 prompt preview
2. TWM-145 成功生成 prompt preview
3. --card-key 必填
4. card_key 不存在返回错误
5. dangerous output path rejected
6. 不生成 semantic ops JSON
7. 不调用 LLM
8. op inventory 包含当前支持 ops
9. unsupported pattern detection
10. original JSON unchanged
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "build_semantic_extraction_prompt.py"

CHINESE_DATA = ROOT / "card_chinese_data.json"
CACHE_DATA = ROOT / "card_data_cache.json"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _load_script_module():
    spec = importlib.util.spec_from_file_location(
        "build_semantic_extraction_prompt", SCRIPT_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load script: {SCRIPT_PATH}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["build_semantic_extraction_prompt"] = mod
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


def _make_input_preview(cards: list[dict[str, Any]]) -> dict[str, Any]:
    """构建符合 build_semantic_extraction_input.py 格式的 input preview JSON。"""
    return {
        "meta": {
            "dry_run": True,
            "network_enabled": False,
            "calls_llm": False,
            "writes_original_cache": False,
            "writes_normalized_cache": False,
            "writes_semantic_ops_json": False,
            "writes_prompt": False,
            "schema_version": "semantic_extraction_input_preview.v1",
        },
        "summary": {
            "input_application_count": len(cards),
            "selected_count": len(cards),
            "ready_count": len(cards),
            "not_ready_count": 0,
            "error_count": 0,
            "warning_count": 0,
        },
        "op_inventory": {
            "allowed_ops": ["move_cards", "discard_cards", "draw_cards", "mark_supporter_played"],
            "disallowed_patterns": ["choice", "optional"],
        },
        "cards": cards,
    }


def _card_entry(
    card_key: str,
    name_en: str = "",
    name_zh: str = "",
    set_code: str = "SSH",
    number: str = "178",
    local_file: str = "ptcg/cards/SSH/ssh178professorsresearch.py",
    rules_text: str = "",
    prompt_ready: bool = True,
) -> dict[str, Any]:
    """创建一个 semantic input card entry fixture。"""
    return {
        "card_key": card_key,
        "identity": {
            "card_key": card_key,
            "name_en": name_en,
            "name_zh": name_zh,
            "set_code": set_code,
            "number": number,
        },
        "classification": {
            "card_supertype": "Trainer",
            "trainer_subtype": "Supporter",
            "classification_source": "local_class",
            "classification_confidence": "high",
        },
        "local_file": local_file,
        "normalized_text": {
            "rules_text_zh": rules_text,
            "trainer_text_zh": rules_text,
            "full_text_zh": rules_text,
        },
        "quality_flags": {
            "prompt_ready": prompt_ready,
            "missing_rules_text": False,
        },
        "provenance_summary": {
            "field_source_map_keys": ["text.rules_text_zh"],
            "sources": [{"id": "card_chinese_data", "type": "json"}],
            "refetch_source": "tcg.mik.moe card-detail",
        },
        "application_summary": {
            "applied_fields": ["text.rules_text_zh"],
            "skipped_fields": [],
            "warnings": [],
            "errors": [],
        },
        "semantic_extraction_task": {
            "task_type": "supporter_effect_to_semantic_ops",
            "expected_output_kind": "semantic_ops_draft",
            "must_not_emit_final_json": True,
            "must_preserve_legacy_behavior": True,
        },
        "known_runtime_support": {
            "available_ops": [
                "move_cards",
                "discard_cards",
                "draw_cards",
                "mark_supporter_played",
            ],
        },
    }


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# 1. SSH-178 成功生成 prompt preview
# ---------------------------------------------------------------------------


def test_ssh178_prompt_preview(tmp_path: Path):
    """SSH-178 prompt_text 包含关键内容。"""
    input_path = tmp_path / "input_preview.json"
    preview = _make_input_preview([
        _card_entry(
            "SSH-178",
            name_en="Professor's Research",
            name_zh="博士的研究",
            rules_text="将自己的所有手牌丢弃，然后从牌库上方抽取7张。",
        ),
    ])
    input_path.write_text(json.dumps(preview, ensure_ascii=False), encoding="utf-8")

    output_path = tmp_path / "ssh178_prompt_preview.json"

    exit_code, output = _run_main(
        "--input-preview", str(input_path),
        "--card-key", "SSH-178",
        "--output-prompt-preview", str(output_path),
    )
    assert exit_code == 0

    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert data["card_key"] == "SSH-178"
    assert data["prompt_ready"] is True
    assert data["meta"]["calls_llm"] is False
    assert data["meta"]["writes_semantic_ops_json"] is False

    prompt_text = data["prompt_preview"]["prompt_text"]
    assert "博士的研究" in prompt_text or "SSH-178" in prompt_text
    assert "抽取7张" in prompt_text
    assert "discard_cards" in prompt_text
    assert "draw_cards" in prompt_text
    assert "mark_supporter_played" in prompt_text
    assert "must_not_emit_final_json" in prompt_text or "不输出最终" in prompt_text or "不得生成最终" in prompt_text


# ---------------------------------------------------------------------------
# 2. TWM-145 成功生成 prompt preview
# ---------------------------------------------------------------------------


def test_twm145_prompt_preview(tmp_path: Path):
    """TWM-145 prompt_text 包含 Carmine 相关内容。"""
    input_path = tmp_path / "input_preview.json"
    preview = _make_input_preview([
        _card_entry(
            "TWM-145",
            name_en="Carmine",
            name_zh="丹瑜",
            set_code="TWM",
            number="145",
            local_file="ptcg/cards/TWM/twm145carmine.py",
            rules_text="将自己的所有手牌丢弃，然后从自己的牌库上方抽取5张。",
        ),
    ])
    input_path.write_text(json.dumps(preview, ensure_ascii=False), encoding="utf-8")

    output_path = tmp_path / "twm145_prompt_preview.json"

    exit_code, output = _run_main(
        "--input-preview", str(input_path),
        "--card-key", "TWM-145",
        "--output-prompt-preview", str(output_path),
    )
    assert exit_code == 0

    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert data["card_key"] == "TWM-145"
    assert data["prompt_ready"] is True

    prompt_text = data["prompt_preview"]["prompt_text"]
    assert "丹瑜" in prompt_text or "Carmine" in prompt_text
    assert "抽取5张" in prompt_text
    assert "mark_supporter_played" in prompt_text


# ---------------------------------------------------------------------------
# 3. --card-key 必填
# ---------------------------------------------------------------------------


def test_card_key_required(tmp_path: Path):
    """不传 --card-key 应该 exit code 非 0 或提示错误。"""
    input_path = tmp_path / "input_preview.json"
    preview = _make_input_preview([_card_entry("SSH-178")])
    input_path.write_text(json.dumps(preview, ensure_ascii=False), encoding="utf-8")

    # 不传 --card-key
    exit_code, output = _run_main(
        "--input-preview", str(input_path),
        "--card-key", "",
    )
    # argparse required 会触发 SystemExit，或者我们的手动检查返回非0
    assert (
        exit_code != 0
        or "card-key" in output.lower()
        or "required" in output.lower()
    )


# ---------------------------------------------------------------------------
# 4. card_key 不存在
# ---------------------------------------------------------------------------


def test_card_key_not_found(tmp_path: Path):
    """card_key 不存在返回错误，不写输出文件。"""
    input_path = tmp_path / "input_preview.json"
    preview = _make_input_preview([_card_entry("SSH-178")])
    input_path.write_text(json.dumps(preview, ensure_ascii=False), encoding="utf-8")

    output_path = tmp_path / "not_found_preview.json"

    exit_code, output = _run_main(
        "--input-preview", str(input_path),
        "--card-key", "UNKNOWN-999",
        "--output-prompt-preview", str(output_path),
    )
    assert exit_code != 0
    assert "not found" in output.lower() or "找不到" in output or "UNKNOWN" in output


# ---------------------------------------------------------------------------
# 5. dangerous output path rejected
# ---------------------------------------------------------------------------


def test_dangerous_path_semantic_ops_json(tmp_path: Path):
    """禁止 --output-prompt-preview semantic_ops.json。"""
    input_path = tmp_path / "input_preview.json"
    preview = _make_input_preview([_card_entry("SSH-178")])
    input_path.write_text(json.dumps(preview, ensure_ascii=False), encoding="utf-8")

    exit_code, output = _run_main(
        "--input-preview", str(input_path),
        "--card-key", "SSH-178",
        "--output-prompt-preview", "semantic_ops.json",
    )
    assert exit_code != 0
    assert "禁止" in output


def test_dangerous_path_prompt_md(tmp_path: Path):
    """禁止 --output-prompt-preview prompt.md。"""
    input_path = tmp_path / "input_preview.json"
    preview = _make_input_preview([_card_entry("SSH-178")])
    input_path.write_text(json.dumps(preview, ensure_ascii=False), encoding="utf-8")

    exit_code, output = _run_main(
        "--input-preview", str(input_path),
        "--card-key", "SSH-178",
        "--output-prompt-preview", "prompt.md",
    )
    assert exit_code != 0
    assert "禁止" in output


def test_dangerous_path_prompts_dir(tmp_path: Path):
    """禁止 --output-prompt-preview prompts/test.md。"""
    input_path = tmp_path / "input_preview.json"
    preview = _make_input_preview([_card_entry("SSH-178")])
    input_path.write_text(json.dumps(preview, ensure_ascii=False), encoding="utf-8")

    exit_code, output = _run_main(
        "--input-preview", str(input_path),
        "--card-key", "SSH-178",
        "--output-prompt-preview", "prompts/test.md",
    )
    assert exit_code != 0
    assert "禁止" in output


def test_dangerous_path_normalized_card_text(tmp_path: Path):
    """禁止 --output-prompt-preview data/normalized_card_text.json。"""
    input_path = tmp_path / "input_preview.json"
    preview = _make_input_preview([_card_entry("SSH-178")])
    input_path.write_text(json.dumps(preview, ensure_ascii=False), encoding="utf-8")

    exit_code, output = _run_main(
        "--input-preview", str(input_path),
        "--card-key", "SSH-178",
        "--output-prompt-preview", "data/normalized_card_text.json",
    )
    assert exit_code != 0
    assert "禁止" in output


# ---------------------------------------------------------------------------
# 6. 不生成 semantic ops JSON
# ---------------------------------------------------------------------------


def test_no_semantic_ops_json_generated(tmp_path: Path):
    """output 中不含 semantic_ops 或 final_ops 字段。"""
    from ptcg.data_sources.semantic_extraction_prompt import (
        build_semantic_extraction_prompt_preview,
    )

    preview = _make_input_preview([_card_entry("SSH-178")])
    result = build_semantic_extraction_prompt_preview(
        preview, card_key="SSH-178"
    )

    assert result["meta"]["writes_semantic_ops_json"] is False
    assert "semantic_ops" not in result
    assert "final_ops" not in result
    prompt_preview = result.get("prompt_preview", {})
    assert "semantic_ops" not in prompt_preview
    assert "final_ops" not in prompt_preview


# ---------------------------------------------------------------------------
# 7. 不调用 LLM
# ---------------------------------------------------------------------------


def test_no_llm_imports():
    """核心模块和 CLI 不 import LLM 库。"""
    core_path = ROOT / "ptcg" / "data_sources" / "semantic_extraction_prompt.py"
    core_source = core_path.read_text(encoding="utf-8")

    forbidden_imports = [
        "import openai",
        "import anthropic",
        "import google.generativeai",
    ]

    for forbidden in forbidden_imports:
        assert forbidden not in core_source, f"核心模块不应导入 {forbidden}"

    cli_source = SCRIPT_PATH.read_text(encoding="utf-8")
    for forbidden in forbidden_imports:
        assert forbidden not in cli_source, f"CLI 不应导入 {forbidden}"


def test_meta_calls_llm_false(tmp_path: Path):
    """meta.calls_llm=false。"""
    input_path = tmp_path / "input_preview.json"
    preview = _make_input_preview([_card_entry("SSH-178")])
    input_path.write_text(json.dumps(preview, ensure_ascii=False), encoding="utf-8")

    output_path = tmp_path / "prompt_preview.json"

    exit_code, _ = _run_main(
        "--input-preview", str(input_path),
        "--card-key", "SSH-178",
        "--output-prompt-preview", str(output_path),
    )
    assert exit_code == 0

    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert data["meta"]["calls_llm"] is False


# ---------------------------------------------------------------------------
# 8. op inventory 包含当前支持 ops
# ---------------------------------------------------------------------------


def test_op_inventory_in_prompt(tmp_path: Path):
    """prompt_text 中包含 move_cards / discard_cards / draw_cards / mark_supporter_played。"""
    input_path = tmp_path / "input_preview.json"
    preview = _make_input_preview([_card_entry("SSH-178")])
    input_path.write_text(json.dumps(preview, ensure_ascii=False), encoding="utf-8")

    output_path = tmp_path / "prompt_preview.json"

    exit_code, _ = _run_main(
        "--input-preview", str(input_path),
        "--card-key", "SSH-178",
        "--output-prompt-preview", str(output_path),
    )
    assert exit_code == 0

    data = json.loads(output_path.read_text(encoding="utf-8"))
    available = data["prompt_preview"]["available_ops"]
    assert "move_cards" in available
    assert "discard_cards" in available
    assert "draw_cards" in available
    assert "mark_supporter_played" in available


# ---------------------------------------------------------------------------
# 9. unsupported pattern detection
# ---------------------------------------------------------------------------


def test_unsupported_pattern_detection(tmp_path: Path):
    """含"选择"、"可以"等关键词时，unsupported_or_needs_manual_review=true。"""
    from ptcg.data_sources.semantic_extraction_prompt import (
        build_semantic_extraction_prompt_preview,
    )

    preview = _make_input_preview([
        _card_entry(
            "TEST-001",
            name_zh="测试卡",
            rules_text="从牌库中选择一张卡加入手牌。可以查看牌库。",
        ),
    ])
    result = build_semantic_extraction_prompt_preview(
        preview, card_key="TEST-001"
    )

    assert result["unsupported_or_needs_manual_review"] is True
    reasons = result["unsupported_reasons"]
    assert len(reasons) > 0
    # 应该检测到 "选择"、"可以"、"从牌库选择"、"查看牌库"
    detected = " ".join(reasons)
    assert "选择" in detected or "choice" in detected.lower()


def test_no_unsupported_for_simple_text(tmp_path: Path):
    """不含 unsupported 关键词的文本不触发标记。"""
    from ptcg.data_sources.semantic_extraction_prompt import (
        build_semantic_extraction_prompt_preview,
    )

    preview = _make_input_preview([
        _card_entry(
            "SSH-178",
            name_zh="博士的研究",
            rules_text="将自己的所有手牌丢弃，然后从牌库上方抽取7张。",
        ),
    ])
    result = build_semantic_extraction_prompt_preview(
        preview, card_key="SSH-178"
    )

    assert result["unsupported_or_needs_manual_review"] is False
    assert result["unsupported_reasons"] == []


# ---------------------------------------------------------------------------
# 10. original JSON unchanged
# ---------------------------------------------------------------------------


def test_original_json_unchanged(tmp_path: Path):
    """card_chinese_data.json / card_data_cache.json 内容不变。"""
    sha_cn_before = _file_sha256(CHINESE_DATA)
    sha_cache_before = _file_sha256(CACHE_DATA)

    input_path = tmp_path / "input_preview.json"
    preview = _make_input_preview([_card_entry("SSH-178")])
    input_path.write_text(json.dumps(preview, ensure_ascii=False), encoding="utf-8")

    output_path = tmp_path / "prompt_preview.json"
    exit_code, _ = _run_main(
        "--input-preview", str(input_path),
        "--card-key", "SSH-178",
        "--output-prompt-preview", str(output_path),
    )
    assert exit_code == 0

    sha_cn_after = _file_sha256(CHINESE_DATA)
    sha_cache_after = _file_sha256(CACHE_DATA)

    assert sha_cn_before == sha_cn_after
    assert sha_cache_before == sha_cache_after


# ---------------------------------------------------------------------------
# 11. 默认 stdout 模式不写文件
# ---------------------------------------------------------------------------


def test_default_stdout_no_file_write(tmp_path: Path):
    """不传 --output-prompt-preview 不应产生任何文件。"""
    input_path = tmp_path / "input_preview.json"
    preview = _make_input_preview([_card_entry("SSH-178")])
    input_path.write_text(json.dumps(preview, ensure_ascii=False), encoding="utf-8")

    exit_code, output = _run_main(
        "--input-preview", str(input_path),
        "--card-key", "SSH-178",
    )
    assert exit_code == 0
    assert "单卡 semantic extraction prompt preview 完成" in output
    assert "calls_llm" in output
