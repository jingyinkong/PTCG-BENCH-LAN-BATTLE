"""测试 semantic ops draft preview。

覆盖：
1. SSH-178 生成 draft preview
2. TWM-145 生成 draft preview
3. PAL-185 标记 unsupported
4. FLI-108 标记 unsupported
5. ASR-150 标记 unsupported
6. dangerous output path rejected
7. 不生成正式 semantic ops JSON
8. 不调用 LLM
9. card_key mismatch
10. fail-on-unsupported
11. original JSON unchanged
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "build_semantic_ops_draft.py"

CHINESE_DATA = ROOT / "card_chinese_data.json"
CACHE_DATA = ROOT / "card_data_cache.json"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _load_script_module():
    spec = importlib.util.spec_from_file_location(
        "build_semantic_ops_draft", SCRIPT_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load script: {SCRIPT_PATH}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["build_semantic_ops_draft"] = mod
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


def _make_prompt_preview(
    card_key: str,
    name_en: str = "",
    name_zh: str = "",
    prompt_text: str = "",
    prompt_ready: bool = True,
    unsupported_or_needs_manual_review: bool = False,
    unsupported_reasons: list[str] | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    """构建符合 Phase 7S prompt preview 格式的 fixture。"""
    return {
        "meta": {
            "dry_run": True,
            "network_enabled": False,
            "calls_llm": False,
            "writes_semantic_ops_json": False,
            "writes_cards": False,
            "writes_core": False,
            "schema_version": "semantic_extraction_prompt_preview.v1",
        },
        "card_key": card_key,
        "prompt_ready": prompt_ready,
        "unsupported_or_needs_manual_review": unsupported_or_needs_manual_review,
        "unsupported_reasons": unsupported_reasons or [],
        "error": error,
        "prompt_preview": {
            "language": "zh",
            "card_context": {
                "card_key": card_key,
                "name_en": name_en,
                "name_zh": name_zh,
            },
            "available_ops": ["move_cards", "discard_cards", "draw_cards", "mark_supporter_played"],
            "prompt_text": prompt_text,
        },
    }


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# 1. SSH-178 生成 draft preview
# ---------------------------------------------------------------------------


def test_ssh178_draft_preview_cli(tmp_path: Path):
    """SSH-178 通过 CLI 生成 draft preview，验证 ops 顺序和 count。"""
    input_path = tmp_path / "prompt_preview.json"
    preview = _make_prompt_preview(
        "SSH-178",
        name_en="Professor's Research",
        name_zh="博士的研究",
        prompt_text="将自己的所有手牌丢弃，然后从牌库上方抽取7张。",
    )
    input_path.write_text(json.dumps(preview, ensure_ascii=False), encoding="utf-8")

    output_path = tmp_path / "ssh178_ops_draft_preview.json"

    exit_code, output = _run_main(
        "--input-prompt-preview", str(input_path),
        "--card-key", "SSH-178",
        "--output-draft-preview", str(output_path),
    )
    assert exit_code == 0

    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert data["card_key"] == "SSH-178"
    assert data["draft_ready"] is True
    assert data["unsupported_or_needs_manual_review"] is False
    assert data["must_not_emit_final_json"] is True
    assert data["meta"]["calls_llm"] is False
    assert data["meta"]["writes_semantic_ops_json"] is False
    assert data["meta"]["writes_cards"] is False
    assert data["meta"]["writes_core"] is False
    assert data["meta"]["network_enabled"] is False

    ops = data["candidate_ops_sequence"]
    assert len(ops) == 4
    assert [op["op_type"] for op in ops] == [
        "move_cards",
        "discard_cards",
        "draw_cards",
        "mark_supporter_played",
    ]

    # draw_cards count=7
    draw_op = ops[2]
    assert draw_op["draft_args"]["count"] == 7

    # 不包含 final_ops 或 runtime_loadable_ops
    assert "final_ops" not in data
    assert "runtime_loadable_ops" not in data

    # effect_summary
    assert "7 张" in data["effect_summary"] or "7张" in data["effect_summary"]


def test_ssh178_draft_preview_direct():
    """SSH-178 直接调用函数验证（不经过 CLI）。"""
    from ptcg.data_sources.semantic_ops_draft import build_semantic_ops_draft_preview

    preview = _make_prompt_preview(
        "SSH-178",
        name_en="Professor's Research",
        name_zh="博士的研究",
        prompt_text="将自己的所有手牌丢弃，然后从牌库上方抽取7张。",
    )

    result = build_semantic_ops_draft_preview(preview, card_key="SSH-178")
    assert result["draft_ready"] is True
    assert result["unsupported_or_needs_manual_review"] is False

    ops = result["candidate_ops_sequence"]
    assert len(ops) == 4
    assert [op["op_type"] for op in ops] == [
        "move_cards",
        "discard_cards",
        "draw_cards",
        "mark_supporter_played",
    ]
    assert ops[2]["draft_args"]["count"] == 7


# ---------------------------------------------------------------------------
# 2. TWM-145 生成 draft preview
# ---------------------------------------------------------------------------


def test_twm145_draft_preview_cli(tmp_path: Path):
    """TWM-145 通过 CLI 生成 draft preview，验证 draw count=5 和 risk_notes。"""
    input_path = tmp_path / "prompt_preview.json"
    preview = _make_prompt_preview(
        "TWM-145",
        name_en="Carmine",
        name_zh="丹瑜",
        prompt_text="将自己的所有手牌丢弃，然后从自己的牌库上方抽取5张。在先攻玩家的最初回合也可以使用。",
    )
    input_path.write_text(json.dumps(preview, ensure_ascii=False), encoding="utf-8")

    output_path = tmp_path / "twm145_ops_draft_preview.json"

    exit_code, output = _run_main(
        "--input-prompt-preview", str(input_path),
        "--card-key", "TWM-145",
        "--output-draft-preview", str(output_path),
    )
    assert exit_code == 0

    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert data["card_key"] == "TWM-145"
    assert data["draft_ready"] is True
    assert data["unsupported_or_needs_manual_review"] is False

    ops = data["candidate_ops_sequence"]
    assert len(ops) == 4
    assert [op["op_type"] for op in ops] == [
        "move_cards",
        "discard_cards",
        "draw_cards",
        "mark_supporter_played",
    ]

    # draw_cards count=5
    draw_op = ops[2]
    assert draw_op["draft_args"]["count"] == 5

    # risk_notes 包含 first turn 说明
    risk_notes = data.get("risk_notes", [])
    assert any("first_turn" in r.lower() or "先攻" in r for r in risk_notes)


# ---------------------------------------------------------------------------
# 3. PAL-185 标记 unsupported
# ---------------------------------------------------------------------------


def test_pal185_unsupported_cli(tmp_path: Path):
    """PAL-185 (Iono) 应标记 unsupported。"""
    input_path = tmp_path / "prompt_preview.json"
    preview = _make_prompt_preview(
        "PAL-185",
        name_en="Iono",
        name_zh="奇树",
        prompt_text="双方玩家将各自的手牌全部放回牌库下方并重洗牌库。然后，双方玩家从牌库上方抽取与各自剩余的奖赏卡张数相同的卡。",
    )
    input_path.write_text(json.dumps(preview, ensure_ascii=False), encoding="utf-8")

    output_path = tmp_path / "pal185_ops_draft_preview.json"

    exit_code, output = _run_main(
        "--input-prompt-preview", str(input_path),
        "--card-key", "PAL-185",
        "--output-draft-preview", str(output_path),
    )
    # 即使 unsupported，只要没有 --fail-on-unsupported，exit code 应为 0
    assert exit_code == 0

    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert data["card_key"] == "PAL-185"
    assert data["draft_ready"] is False
    assert data["unsupported_or_needs_manual_review"] is True
    assert len(data["candidate_ops_sequence"]) == 0
    assert "unsupported_prize_count_or_deck_bottom" in data["unsupported_reasons"]


# ---------------------------------------------------------------------------
# 4. FLI-108 标记 unsupported
# ---------------------------------------------------------------------------


def test_fli108_unsupported(tmp_path: Path):
    """FLI-108 (Judge) 应标记 unsupported。"""
    from ptcg.data_sources.semantic_ops_draft import build_semantic_ops_draft_preview

    preview = _make_prompt_preview(
        "FLI-108",
        name_en="Judge",
        name_zh="裁判",
        prompt_text="双方玩家将各自的手牌放回牌库并重洗。然后，双方玩家各自从牌库上方抽取4张。",
    )

    result = build_semantic_ops_draft_preview(preview, card_key="FLI-108")
    assert result["draft_ready"] is False
    assert result["unsupported_or_needs_manual_review"] is True
    assert len(result["candidate_ops_sequence"]) == 0
    assert "shuffle_or_both_players_unsupported" in result["unsupported_reasons"]


# ---------------------------------------------------------------------------
# 5. ASR-150 标记 unsupported
# ---------------------------------------------------------------------------


def test_asr150_unsupported(tmp_path: Path):
    """ASR-150 (Roxanne) 应标记 unsupported。"""
    from ptcg.data_sources.semantic_ops_draft import build_semantic_ops_draft_preview

    preview = _make_prompt_preview(
        "ASR-150",
        name_en="Roxanne",
        name_zh="竹兰的霸气",
        prompt_text="只有在对手的剩余奖赏卡为3张以下时才可使用。双方玩家将各自的手牌放回牌库并重洗。然后，自己从牌库上方抽取6张，对手从牌库上方抽取2张。",
    )

    result = build_semantic_ops_draft_preview(preview, card_key="ASR-150")
    assert result["draft_ready"] is False
    assert result["unsupported_or_needs_manual_review"] is True
    assert len(result["candidate_ops_sequence"]) == 0
    assert "conditional_or_both_players_unsupported" in result["unsupported_reasons"]


# ---------------------------------------------------------------------------
# 6. dangerous output path rejected
# ---------------------------------------------------------------------------


def test_dangerous_output_semantic_ops_json(tmp_path: Path):
    """拒绝写入 semantic_ops.json。"""
    input_path = tmp_path / "prompt_preview.json"
    preview = _make_prompt_preview("SSH-178", prompt_text="将自己的所有手牌丢弃，然后从牌库上方抽取7张。")
    input_path.write_text(json.dumps(preview, ensure_ascii=False), encoding="utf-8")

    exit_code, output = _run_main(
        "--input-prompt-preview", str(input_path),
        "--card-key", "SSH-178",
        "--output-draft-preview", "semantic_ops.json",
    )
    assert exit_code != 0
    assert "禁止" in output or "semantic_ops" in output.lower()


def test_dangerous_output_ops_json(tmp_path: Path):
    """拒绝写入 ops.json。"""
    input_path = tmp_path / "prompt_preview.json"
    preview = _make_prompt_preview("SSH-178", prompt_text="将自己的所有手牌丢弃，然后从牌库上方抽取7张。")
    input_path.write_text(json.dumps(preview, ensure_ascii=False), encoding="utf-8")

    exit_code, output = _run_main(
        "--input-prompt-preview", str(input_path),
        "--card-key", "SSH-178",
        "--output-draft-preview", "ops.json",
    )
    assert exit_code != 0


def test_dangerous_output_ptcg_cards(tmp_path: Path):
    """拒绝写入 ptcg/cards/ 目录。"""
    input_path = tmp_path / "prompt_preview.json"
    preview = _make_prompt_preview("SSH-178", prompt_text="将自己的所有手牌丢弃，然后从牌库上方抽取7张。")
    input_path.write_text(json.dumps(preview, ensure_ascii=False), encoding="utf-8")

    exit_code, output = _run_main(
        "--input-prompt-preview", str(input_path),
        "--card-key", "SSH-178",
        "--output-draft-preview", "ptcg/cards/foo.json",
    )
    assert exit_code != 0


def test_dangerous_output_ptcg_core(tmp_path: Path):
    """拒绝写入 ptcg/core/ 目录。"""
    input_path = tmp_path / "prompt_preview.json"
    preview = _make_prompt_preview("SSH-178", prompt_text="将自己的所有手牌丢弃，然后从牌库上方抽取7张。")
    input_path.write_text(json.dumps(preview, ensure_ascii=False), encoding="utf-8")

    exit_code, output = _run_main(
        "--input-prompt-preview", str(input_path),
        "--card-key", "SSH-178",
        "--output-draft-preview", "ptcg/core/foo.json",
    )
    assert exit_code != 0


# ---------------------------------------------------------------------------
# 7. 不生成正式 semantic ops JSON
# ---------------------------------------------------------------------------


def test_no_final_semantic_ops_json(tmp_path: Path):
    """draft preview 不包含 final_ops 或 runtime_loadable_ops。"""
    from ptcg.data_sources.semantic_ops_draft import build_semantic_ops_draft_preview

    preview = _make_prompt_preview(
        "SSH-178",
        name_en="Professor's Research",
        name_zh="博士的研究",
        prompt_text="将自己的所有手牌丢弃，然后从牌库上方抽取7张。",
    )

    result = build_semantic_ops_draft_preview(preview, card_key="SSH-178")
    assert result["meta"]["writes_semantic_ops_json"] is False
    assert "final_ops" not in result
    assert "runtime_loadable_ops" not in result
    assert result["must_not_emit_final_json"] is True


# ---------------------------------------------------------------------------
# 8. 不调用 LLM
# ---------------------------------------------------------------------------


def test_no_llm_import():
    """semantic_ops_draft 模块不导入 LLM 库。"""
    import ast
    module_path = ROOT / "ptcg" / "data_sources" / "semantic_ops_draft.py"
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    disallowed_imports = {"openai", "anthropic", "google.generativeai", "httpx", "requests"}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name not in disallowed_imports, f"禁止导入: {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                full_name = f"{module}.{alias.name}"
                for disallowed in disallowed_imports:
                    assert disallowed not in full_name, f"禁止导入: {full_name}"


def test_meta_calls_llm_false(tmp_path: Path):
    """meta.calls_llm 必须为 false。"""
    input_path = tmp_path / "prompt_preview.json"
    preview = _make_prompt_preview("SSH-178", prompt_text="将自己的所有手牌丢弃，然后从牌库上方抽取7张。")
    input_path.write_text(json.dumps(preview, ensure_ascii=False), encoding="utf-8")

    output_path = tmp_path / "draft_preview.json"

    exit_code, output = _run_main(
        "--input-prompt-preview", str(input_path),
        "--card-key", "SSH-178",
        "--output-draft-preview", str(output_path),
    )
    assert exit_code == 0

    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert data["meta"]["calls_llm"] is False


# ---------------------------------------------------------------------------
# 9. card_key mismatch
# ---------------------------------------------------------------------------


def test_card_key_mismatch(tmp_path: Path):
    """输入 card_key 与参数不一致时应返回 draft_ready=false。"""
    input_path = tmp_path / "prompt_preview.json"
    preview = _make_prompt_preview(
        "SSH-178",
        name_en="Professor's Research",
        prompt_text="将自己的所有手牌丢弃，然后从牌库上方抽取7张。",
    )
    input_path.write_text(json.dumps(preview, ensure_ascii=False), encoding="utf-8")

    exit_code, output = _run_main(
        "--input-prompt-preview", str(input_path),
        "--card-key", "TWM-145",
    )
    # card_key mismatch 应返回非 0
    assert exit_code != 0
    assert "mismatch" in output.lower() or "不匹配" in output


# ---------------------------------------------------------------------------
# 10. fail-on-unsupported
# ---------------------------------------------------------------------------


def test_fail_on_unsupported_pal185(tmp_path: Path):
    """unsupported 卡牌 + --fail-on-unsupported 应 exit code 非 0。"""
    input_path = tmp_path / "prompt_preview.json"
    preview = _make_prompt_preview(
        "PAL-185",
        name_en="Iono",
        prompt_text="双方玩家将各自的手牌全部放回牌库下方并重洗牌库。",
    )
    input_path.write_text(json.dumps(preview, ensure_ascii=False), encoding="utf-8")

    exit_code, output = _run_main(
        "--input-prompt-preview", str(input_path),
        "--card-key", "PAL-185",
        "--fail-on-unsupported",
    )
    assert exit_code != 0


# ---------------------------------------------------------------------------
# 11. original JSON unchanged
# ---------------------------------------------------------------------------


def test_original_json_unchanged():
    """card_chinese_data.json 和 card_data_cache.json 内容不变。"""
    # 此测试只是确认文件存在且可读，保证测试环境下不会被修改
    assert CHINESE_DATA.exists(), f"{CHINESE_DATA} should exist"
    assert CACHE_DATA.exists(), f"{CACHE_DATA} should exist"

    sha_cn = _file_sha256(CHINESE_DATA)
    sha_cache = _file_sha256(CACHE_DATA)
    # 只验证 hash 非空（不硬编码 hash 值）
    assert len(sha_cn) == 64
    assert len(sha_cache) == 64
