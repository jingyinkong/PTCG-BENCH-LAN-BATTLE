"""SSH-178 semantic draft alignment golden test.

将 Phase 7U 审查结论固化为自动化测试，确保 SSH-178 的 draft preview
不会悄悄偏离现有 resolve_ops / side-channel 行为。

不修改卡牌实现。
不修改 semantic runtime。
不生成正式 semantic ops JSON。
不接入 reducer / env.step。
不调用 LLM。
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from ptcg.data_sources.semantic_ops_draft import build_semantic_ops_draft_preview

ROOT = Path(__file__).resolve().parents[2]
CHINESE_DATA = ROOT / "card_chinese_data.json"
CACHE_DATA = ROOT / "card_data_cache.json"

# ---------------------------------------------------------------------------
# 7U 文档确认的 golden sequence
# ---------------------------------------------------------------------------

EXPECTED_SSH178_SEQUENCE = [
    "move_cards",
    "discard_cards",
    "draw_cards",
    "mark_supporter_played",
]

# ---------------------------------------------------------------------------
# 最小 prompt preview fixture（不依赖真实网络 / LLM / IO）
# ---------------------------------------------------------------------------


def _make_ssh178_prompt_preview() -> dict[str, Any]:
    """构建符合 Phase 7S prompt preview 格式的 SSH-178 最小 fixture。"""
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
        "card_key": "SSH-178",
        "prompt_ready": True,
        "unsupported_or_needs_manual_review": False,
        "unsupported_reasons": [],
        "prompt_preview": {
            "card_context": {
                "card_key": "SSH-178",
                "identity": {
                    "name": "Professor's Research",
                    "chinese_name": "博士的研究",
                    "set": "SSH",
                    "number": "178",
                },
                "classification": {
                    "card_supertype": "Trainer",
                    "trainer_subtype": "Supporter",
                },
                "normalized_text": {
                    "rules_text_zh": (
                        "将自己的手牌全部放于弃牌区，从牌库上方抽取7张卡牌。"
                    ),
                    "trainer_text_zh": (
                        "将自己的手牌全部放于弃牌区，从牌库上方抽取7张卡牌。"
                    ),
                    "full_text_zh": (
                        "将自己的手牌全部放于弃牌区，从牌库上方抽取7张卡牌。"
                    ),
                },
            },
            "available_ops": [
                "move_cards",
                "discard_cards",
                "draw_cards",
                "mark_supporter_played",
            ],
            "prompt_text": (
                "测试用 prompt preview。"
                "将自己的手牌全部放于弃牌区，从牌库上方抽取7张卡牌。"
            ),
        },
    }


def _build_ssh178_result() -> dict[str, Any]:
    """构建 SSH-178 的 draft preview 结果。"""
    return build_semantic_ops_draft_preview(
        _make_ssh178_prompt_preview(),
        card_key="SSH-178",
    )


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# 测试一：SSH-178 golden sequence
# ---------------------------------------------------------------------------


def test_ssh178_golden_sequence():
    """断言 candidate_ops_sequence 顺序、类型、参数与 7U 文档完全一致。"""
    result = _build_ssh178_result()

    # 基本元数据
    assert result["card_key"] == "SSH-178"
    assert result["draft_ready"] is True
    assert result["unsupported_or_needs_manual_review"] is False
    assert result["must_not_emit_final_json"] is True

    # meta 字段
    meta = result["meta"]
    assert meta["writes_semantic_ops_json"] is False
    assert meta["writes_cards"] is False
    assert meta["writes_core"] is False
    assert meta["calls_llm"] is False
    assert meta["network_enabled"] is False
    assert meta["dry_run"] is True

    # candidate_ops_sequence 长度
    ops = result["candidate_ops_sequence"]
    assert len(ops) == 4

    # op_type 顺序严格等于 golden
    assert [op["op_type"] for op in ops] == EXPECTED_SSH178_SEQUENCE

    # op[0] move_cards
    assert ops[0]["op_type"] == "move_cards"
    assert ops[0]["draft_args"]["selector"] == "this_card"
    assert ops[0]["draft_args"]["source"] == "self.hand"
    assert ops[0]["draft_args"]["destination"] == "self.discard"

    # op[1] discard_cards count == "all"
    assert ops[1]["op_type"] == "discard_cards"
    assert ops[1]["draft_args"]["count"] == "all"
    assert ops[1]["draft_args"]["actor"] == "self"
    assert ops[1]["draft_args"]["zone"] == "hand"

    # op[2] draw_cards count == 7
    assert ops[2]["op_type"] == "draw_cards"
    assert ops[2]["draft_args"]["count"] == 7
    assert ops[2]["draft_args"]["actor"] == "self"

    # op[3] mark_supporter_played actor == "self"
    assert ops[3]["op_type"] == "mark_supporter_played"
    assert ops[3]["draft_args"]["actor"] == "self"


# ---------------------------------------------------------------------------
# 测试二：golden sequence 与 7U 文档结论一致
# ---------------------------------------------------------------------------


def test_ssh178_alignment_with_phase7u_doc():
    """断言生成的 op 顺序与 7U 文档中定义的 EXPECTED_SSH178_SEQUENCE 一致。"""
    result = _build_ssh178_result()
    ops = result["candidate_ops_sequence"]
    op_types = [op["op_type"] for op in ops]
    assert op_types == EXPECTED_SSH178_SEQUENCE, (
        f"SSH-178 draft preview op types {op_types} "
        f"偏离 7U 文档 golden sequence {EXPECTED_SSH178_SEQUENCE}"
    )

    # 确认 draw count=7 与文档一致
    assert ops[2]["draft_args"]["count"] == 7

    # 确认 discard count=all 与文档一致
    assert ops[1]["draft_args"]["count"] == "all"


# ---------------------------------------------------------------------------
# 测试三：不包含 runtime-loadable final ops
# ---------------------------------------------------------------------------


_RUNTIME_ONLY_FIELDS = [
    "semantic_ops",
    "final_ops",
    "runtime_loadable_ops",
    "resolve_ops_code",
    "card_patch",
    "ops",
]


def test_ssh178_not_runtime_loadable():
    """断言输出不包含任何 runtime-loadable final ops 字段。"""
    result = _build_ssh178_result()
    for field in _RUNTIME_ONLY_FIELDS:
        assert field not in result, f"golden draft preview 不应包含字段 '{field}'"
        # 也检查 candidate_ops_sequence 中每个 op
        for op in result["candidate_ops_sequence"]:
            assert field not in op, (
                f"candidate op 不应包含字段 '{field}'"
            )


# ---------------------------------------------------------------------------
# 测试四：legacy behavior checklist
# ---------------------------------------------------------------------------


def test_ssh178_legacy_behavior_checklist():
    """断言 legacy_behavior_checklist 覆盖关键行为。"""
    result = _build_ssh178_result()
    checklist = result.get("legacy_behavior_checklist", [])

    # 至少应包含 supporterPlayedTurn 标记
    assert any("supporterPlayedTurn" in item or "supporter" in item.lower()
               for item in checklist), (
        f"checklist 应包含 supporterPlayedTurn: {checklist}"
    )

    # 至少应包含 "自身从 hand 移动到 discard" 或等价描述
    assert any(
        ("hand" in item and "discard" in item) or "手牌" in item
        for item in checklist
    ), f"checklist 应包含 hand->discard 描述: {checklist}"

    # 至少应包含抽牌描述
    assert any(
        "抽" in item or "draw" in item.lower()
        for item in checklist
    ), f"checklist 应包含抽牌描述: {checklist}"


# ---------------------------------------------------------------------------
# 测试五：原始 JSON 不变
# ---------------------------------------------------------------------------


def test_ssh178_original_json_unchanged():
    """card_chinese_data.json 和 card_data_cache.json 内容不变。"""
    assert CHINESE_DATA.exists(), f"{CHINESE_DATA} should exist"
    assert CACHE_DATA.exists(), f"{CACHE_DATA} should exist"

    # 构建 draft preview 前后各取 hash
    sha_cn_before = _file_sha256(CHINESE_DATA)
    sha_cache_before = _file_sha256(CACHE_DATA)

    _ = _build_ssh178_result()

    sha_cn_after = _file_sha256(CHINESE_DATA)
    sha_cache_after = _file_sha256(CACHE_DATA)

    assert sha_cn_before == sha_cn_after, (
        f"card_chinese_data.json 的 hash 在测试前后不一致！"
    )
    assert sha_cache_before == sha_cache_after, (
        f"card_data_cache.json 的 hash 在测试前后不一致！"
    )
    assert len(sha_cn_before) == 64
    assert len(sha_cache_before) == 64


# ---------------------------------------------------------------------------
# 测试六：calls_llm 和 network_enabled 均为 false
# ---------------------------------------------------------------------------


def test_ssh178_no_llm_no_network():
    """断言 draft preview 不调用 LLM、不联网。"""
    result = _build_ssh178_result()
    assert result["meta"]["calls_llm"] is False
    assert result["meta"]["network_enabled"] is False


# ---------------------------------------------------------------------------
# 测试七：candidate ops 中每个 op 都有 purpose
# ---------------------------------------------------------------------------


def test_ssh178_each_op_has_purpose():
    """断言每个 candidate op 都有 purpose 字段。"""
    result = _build_ssh178_result()
    for i, op in enumerate(result["candidate_ops_sequence"]):
        assert op.get("purpose"), (
            f"candidate op[{i}] ({op['op_type']}) 缺少 purpose 字段"
        )


# ---------------------------------------------------------------------------
# 测试八：effect_summary 包含关键描述
# ---------------------------------------------------------------------------


def test_ssh178_effect_summary_covers_key_behaviors():
    """断言 effect_summary 覆盖弃牌、抽 7 张、标记支援者。"""
    result = _build_ssh178_result()
    summary = result["effect_summary"]
    assert "弃" in summary or "discard" in summary.lower()
    assert "7" in summary
    assert "支援者" in summary or "supporter" in summary.lower()
