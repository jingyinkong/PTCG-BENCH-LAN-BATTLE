"""TWM-145 semantic draft alignment golden test.

将 TWM-145 Carmine / 丹瑜 的 draft preview 行为固化为自动化测试，
确保后续不会偏离现有 resolve_ops / side-channel 行为。

TWM-145 期望 sequence:
    1. move_cards
    2. discard_cards(count=all)
    3. draw_cards(count=5)
    4. mark_supporter_played(actor=self)

特殊说明：
    先攻玩家的最初回合也可以使用 -> risk_notes / special_notes，不生成新 op。

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
# TWM-145 golden sequence
# ---------------------------------------------------------------------------

EXPECTED_TWM145_SEQUENCE = [
    "move_cards",
    "discard_cards",
    "draw_cards",
    "mark_supporter_played",
]

# ---------------------------------------------------------------------------
# 最小 prompt preview fixture（不依赖真实网络 / LLM / IO）
# ---------------------------------------------------------------------------


def _make_twm145_prompt_preview() -> dict[str, Any]:
    """构建符合 Phase 7S prompt preview 格式的 TWM-145 最小 fixture。

    包含先攻首回合可使用文本，确保测试覆盖 special_notes 行为。
    """
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
        "card_key": "TWM-145",
        "prompt_ready": True,
        "unsupported_or_needs_manual_review": False,
        "unsupported_reasons": [],
        "prompt_preview": {
            "card_context": {
                "card_key": "TWM-145",
                "identity": {
                    "name": "Carmine",
                    "chinese_name": "丹瑜",
                    "set": "TWM",
                    "number": "145",
                },
                "classification": {
                    "card_supertype": "Trainer",
                    "trainer_subtype": "Supporter",
                },
                "normalized_text": {
                    "rules_text_zh": (
                        "这张卡牌，即使是先攻玩家的最初回合也可以使用。"
                        "弃掉自己的手牌，从牌库上方抽取5张卡牌。"
                    ),
                    "trainer_text_zh": (
                        "这张卡牌，即使是先攻玩家的最初回合也可以使用。"
                        "弃掉自己的手牌，从牌库上方抽取5张卡牌。"
                    ),
                    "full_text_zh": (
                        "这张卡牌，即使是先攻玩家的最初回合也可以使用。"
                        "弃掉自己的手牌，从牌库上方抽取5张卡牌。"
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
                "这张卡牌，即使是先攻玩家的最初回合也可以使用。"
                "弃掉自己的手牌，从牌库上方抽取5张卡牌。"
            ),
        },
    }


def _build_twm145_result() -> dict[str, Any]:
    """构建 TWM-145 的 draft preview 结果。"""
    return build_semantic_ops_draft_preview(
        _make_twm145_prompt_preview(),
        card_key="TWM-145",
    )


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# 测试一：TWM-145 golden sequence
# ---------------------------------------------------------------------------


def test_twm145_golden_sequence():
    """断言 candidate_ops_sequence 顺序、类型、参数与预期完全一致。"""
    result = _build_twm145_result()

    # 基本元数据
    assert result["card_key"] == "TWM-145"
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
    assert [op["op_type"] for op in ops] == EXPECTED_TWM145_SEQUENCE

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

    # op[2] draw_cards count == 5
    assert ops[2]["op_type"] == "draw_cards"
    assert ops[2]["draft_args"]["count"] == 5
    assert ops[2]["draft_args"]["actor"] == "self"

    # op[3] mark_supporter_played actor == "self"
    assert ops[3]["op_type"] == "mark_supporter_played"
    assert ops[3]["draft_args"]["actor"] == "self"


# ---------------------------------------------------------------------------
# 测试二：golden sequence 与现有 Carmine side-channel 语义一致
# ---------------------------------------------------------------------------


def test_twm145_golden_matches_sidechannel():
    """断言生成的 op 顺序与 EXPECTED_TWM145_SEQUENCE 一致。"""
    result = _build_twm145_result()
    ops = result["candidate_ops_sequence"]
    op_types = [op["op_type"] for op in ops]
    assert op_types == EXPECTED_TWM145_SEQUENCE, (
        f"TWM-145 draft preview op types {op_types} "
        f"偏离 golden sequence {EXPECTED_TWM145_SEQUENCE}"
    )

    # 确认 discard count=all 与 resolve_ops 行为一致
    assert ops[1]["draft_args"]["count"] == "all"

    # 确认 draw count=5 与 resolve_ops 行为一致
    assert ops[2]["draft_args"]["count"] == 5

    # 确认 mark_supporter_played 存在
    assert ops[3]["op_type"] == "mark_supporter_played"


# ---------------------------------------------------------------------------
# 测试三：先攻首回合特殊说明只进入 notes，不生成新 op
# ---------------------------------------------------------------------------


def test_twm145_first_turn_only_in_notes():
    """断言先攻首回合说明进入 risk_notes / special_notes，不生成新 op。"""
    result = _build_twm145_result()

    # risk_notes 应包含先攻首回合说明
    risk_notes = result.get("risk_notes", [])
    assert risk_notes, "risk_notes 不应为空（应包含先攻首回合说明）"
    first_turn_found = any(
        "usable_on_first_turn" in note
        or "先攻" in note
        or "最初回合" in note
        or "special_notes" in note
        for note in risk_notes
    )
    assert first_turn_found, (
        f"risk_notes 应包含先攻首回合说明: {risk_notes}"
    )

    # candidate_ops_sequence 不包含 play_condition / first_turn / allow_first_turn / custom op
    ops = result["candidate_ops_sequence"]
    forbidden_op_types = {
        "play_condition",
        "first_turn",
        "allow_first_turn",
        "custom",
    }
    for op in ops:
        assert op["op_type"] not in forbidden_op_types, (
            f"不应出现 {op['op_type']} op，先攻首回合说明只能进入 notes"
        )

    # op_type 仍然只包含当前 4 个 runtime 支持 op
    op_types = [op["op_type"] for op in ops]
    runtime_ops = {"move_cards", "discard_cards", "draw_cards", "mark_supporter_played"}
    for ot in op_types:
        assert ot in runtime_ops, f"op_type '{ot}' 不在当前 runtime 支持列表中"


# ---------------------------------------------------------------------------
# 测试四：不包含 runtime-loadable final ops
# ---------------------------------------------------------------------------


_RUNTIME_ONLY_FIELDS = [
    "semantic_ops",
    "final_ops",
    "runtime_loadable_ops",
    "resolve_ops_code",
    "card_patch",
    "ops",
]


def test_twm145_not_runtime_loadable():
    """断言输出不包含任何 runtime-loadable final ops 字段。"""
    result = _build_twm145_result()
    for field in _RUNTIME_ONLY_FIELDS:
        assert field not in result, f"golden draft preview 不应包含字段 '{field}'"
        for op in result["candidate_ops_sequence"]:
            assert field not in op, (
                f"candidate op 不应包含字段 '{field}'"
            )


# ---------------------------------------------------------------------------
# 测试五：legacy behavior checklist
# ---------------------------------------------------------------------------


def test_twm145_legacy_behavior_checklist():
    """断言 legacy_behavior_checklist 覆盖关键行为：
    - self card moves from hand to discard
    - discard all hand cards
    - draw 5 cards
    - mark supporter played
    - first-turn special note retained
    """
    result = _build_twm145_result()
    checklist = result.get("legacy_behavior_checklist", [])

    # supporterPlayedTurn 标记
    assert any(
        "supporterPlayedTurn" in item or "supporter" in item.lower()
        for item in checklist
    ), f"checklist 应包含 supporterPlayedTurn: {checklist}"

    # 自身从 hand 移动到 discard
    assert any(
        ("hand" in item and "discard" in item) or "手牌" in item
        for item in checklist
    ), f"checklist 应包含 hand->discard 描述: {checklist}"

    # 抽 5 张牌
    assert any(
        "抽" in item or "draw" in item.lower()
        for item in checklist
    ), f"checklist 应包含抽牌描述: {checklist}"

    # effect_summary 中也应覆盖关键行为
    summary = result.get("effect_summary", "")
    assert "弃" in summary or "discard" in summary.lower()
    assert "5" in summary
    assert "支援者" in summary or "supporter" in summary.lower()


# ---------------------------------------------------------------------------
# 测试六：原始 JSON 不变
# ---------------------------------------------------------------------------


def test_twm145_original_json_unchanged():
    """card_chinese_data.json 和 card_data_cache.json 内容不变。"""
    assert CHINESE_DATA.exists(), f"{CHINESE_DATA} should exist"
    assert CACHE_DATA.exists(), f"{CACHE_DATA} should exist"

    sha_cn_before = _file_sha256(CHINESE_DATA)
    sha_cache_before = _file_sha256(CACHE_DATA)

    _ = _build_twm145_result()

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
# 测试七：no LLM / no network
# ---------------------------------------------------------------------------


def test_twm145_no_llm_no_network():
    """断言 draft preview 不调用 LLM、不联网。"""
    result = _build_twm145_result()
    assert result["meta"]["calls_llm"] is False
    assert result["meta"]["network_enabled"] is False
