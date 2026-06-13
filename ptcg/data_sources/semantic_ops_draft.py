"""单卡 semantic ops draft preview —— 纯函数，不联网，不调用 LLM。

从 Phase 7S 生成的 prompt preview JSON 中提取指定 card_key 的数据，
使用保守启发式生成 structured semantic ops draft preview。

不生成正式 semantic ops JSON。
不修改 ptcg/cards。
不修改 ptcg/core。
不调用 LLM。
"""

from __future__ import annotations

import copy
from typing import Any

# ---------------------------------------------------------------------------
# 当前支持的 semantic op 清单（与 executor/bridge 保持一致）
# ---------------------------------------------------------------------------

_SUPPORTED_OPS = {
    "move_cards",
    "discard_cards",
    "draw_cards",
    "mark_supporter_played",
}

# ---------------------------------------------------------------------------
# 已知卡牌的启发式规则
# ---------------------------------------------------------------------------

# SSH-178 Professor's Research / 博士的研究
_SSH178_KEYWORDS = [
    "将自己的手牌全部",
    "弃牌区",
    "抽取7张",
]

# 备选关键词
_SSH178_ALT_KEYWORDS = [
    "手牌",
    "弃",
    "抽7",
    "7张",
]

# TWM-145 Carmine / 丹瑜
_TWM145_KEYWORDS = [
    "弃掉自己的手牌",
    "抽取5张",
]

_TWM145_ALT_KEYWORDS = [
    "手牌",
    "弃",
    "抽5",
    "5张",
]

# unsupported 卡牌启发式
_UNSUPPORTED_CONFIG: dict[str, dict[str, Any]] = {
    "PAL-185": {
        "name": "Iono",
        "reasons": ["both_players", "hand_to_deck_bottom", "prize_count_conditional"],
        "label": "unsupported_prize_count_or_deck_bottom",
    },
    "FLI-108": {
        "name": "Judge",
        "reasons": ["both_players", "shuffle_hand_into_deck", "draw_4"],
        "label": "shuffle_or_both_players_unsupported",
    },
    "ASR-150": {
        "name": "Roxanne",
        "reasons": ["both_players", "conditional_prize_count", "hand_back_to_deck"],
        "label": "conditional_or_both_players_unsupported",
    },
}

# Carmine 特殊注释关键词
_FIRST_TURN_KEYWORDS = [
    "先攻",
    "最初回合",
    "第一回合",
    "后攻",
]


# ---------------------------------------------------------------------------
# 文本检测辅助函数
# ---------------------------------------------------------------------------


def _detect_keywords(text: str, keywords: list[str]) -> bool:
    """检查文本是否包含任意一组关键词。（组内全部命中才算匹配）"""
    if not text:
        return False
    return all(kw in text for kw in keywords)


def _detect_any_keyword(text: str, keywords: list[str]) -> bool:
    """检查文本是否包含任一关键词。"""
    if not text:
        return False
    return any(kw in text for kw in keywords)


def _extract_full_text(prompt_preview: dict, card_key: str) -> str:
    """从 prompt preview 中提取卡牌的完整中文文本。"""
    prompt_text = (
        prompt_preview.get("prompt_preview", {})
        .get("prompt_text", "")
    )
    return prompt_text


def _match_card_heuristic(text: str, card_key: str) -> str | None:
    """根据文本和 card_key 匹配已知卡牌启发式规则。

    Returns:
        匹配的卡牌名称标签，或 None。
    """
    # 精确 card_key 匹配（最高优先级）
    if card_key == "SSH-178":
        return "professors_research"
    if card_key == "TWM-145":
        return "carmine"

    # 关键词匹配
    if _detect_keywords(text, _SSH178_KEYWORDS):
        return "professors_research"
    if _detect_keywords(text, _TWM145_KEYWORDS):
        return "carmine"

    return None


# ---------------------------------------------------------------------------
# draft candidate ops 生成
# ---------------------------------------------------------------------------


def _build_professors_research_ops() -> list[dict[str, Any]]:
    """构建 Professor's Research / 博士的研究 的候选 ops 序列。"""
    return [
        {
            "op_type": "move_cards",
            "purpose": "将使用的 Supporter 自身从手牌移动到弃牌区",
            "draft_args": {
                "source": "self.hand",
                "destination": "self.discard",
                "selector": "this_card",
            },
        },
        {
            "op_type": "discard_cards",
            "purpose": "弃掉自己的全部手牌",
            "draft_args": {
                "actor": "self",
                "zone": "hand",
                "count": "all",
            },
        },
        {
            "op_type": "draw_cards",
            "purpose": "抽 7 张牌",
            "draft_args": {
                "actor": "self",
                "count": 7,
            },
        },
        {
            "op_type": "mark_supporter_played",
            "purpose": "标记本回合已使用支援者",
            "draft_args": {
                "actor": "self",
            },
        },
    ]


def _build_carmine_ops() -> list[dict[str, Any]]:
    """构建 Carmine / 丹瑜 的候选 ops 序列。"""
    return [
        {
            "op_type": "move_cards",
            "purpose": "将使用的 Supporter 自身从手牌移动到弃牌区",
            "draft_args": {
                "source": "self.hand",
                "destination": "self.discard",
                "selector": "this_card",
            },
        },
        {
            "op_type": "discard_cards",
            "purpose": "弃掉自己的全部手牌",
            "draft_args": {
                "actor": "self",
                "zone": "hand",
                "count": "all",
            },
        },
        {
            "op_type": "draw_cards",
            "purpose": "抽 5 张牌",
            "draft_args": {
                "actor": "self",
                "count": 5,
            },
        },
        {
            "op_type": "mark_supporter_played",
            "purpose": "标记本回合已使用支援者",
            "draft_args": {
                "actor": "self",
            },
        },
    ]


# ---------------------------------------------------------------------------
# 核心构建函数
# ---------------------------------------------------------------------------


def build_semantic_ops_draft_preview(
    prompt_preview: dict,
    *,
    card_key: str,
    strict_supported_ops: bool = True,
) -> dict:
    """从 Phase 7S prompt preview 生成单卡 semantic ops draft preview。

    Args:
        prompt_preview: Phase 7S build_semantic_extraction_prompt_preview() 的输出。
        card_key: 目标卡牌 key。
        strict_supported_ops: 是否严格检查 op 支持（默认 True）。

    Returns:
        semantic ops draft preview dict。
    """
    source = copy.deepcopy(prompt_preview)

    # 基本 meta
    meta = {
        "dry_run": True,
        "network_enabled": False,
        "calls_llm": False,
        "writes_semantic_ops_json": False,
        "writes_cards": False,
        "writes_core": False,
        "schema_version": "semantic_ops_draft_preview.v1",
    }

    # 校验 card_key 匹配
    source_card_key = source.get("card_key", "")
    if source_card_key and source_card_key != card_key:
        return {
            "meta": meta,
            "card_key": card_key,
            "draft_ready": False,
            "unsupported_or_needs_manual_review": True,
            "unsupported_reasons": [
                f"card_key 不匹配: 输入为 '{source_card_key}'，请求为 '{card_key}'"
            ],
            "effect_summary": "",
            "legacy_behavior_checklist": [],
            "candidate_ops_sequence": [],
            "test_ideas": [],
            "risk_notes": [],
            "must_not_emit_final_json": True,
            "error": f"card_key mismatch: expected '{card_key}', got '{source_card_key}'",
        }

    # 检查 prompt_ready
    prompt_ready = source.get("prompt_ready", False)
    if not prompt_ready:
        return {
            "meta": meta,
            "card_key": card_key,
            "draft_ready": False,
            "unsupported_or_needs_manual_review": False,
            "unsupported_reasons": [],
            "effect_summary": "",
            "legacy_behavior_checklist": [],
            "candidate_ops_sequence": [],
            "test_ideas": [],
            "risk_notes": [],
            "must_not_emit_final_json": True,
            "error": "prompt_ready=false，无法生成 draft preview",
        }

    # 提取文本
    prompt_text = _extract_full_text(source, card_key)
    if not prompt_text:
        return {
            "meta": meta,
            "card_key": card_key,
            "draft_ready": False,
            "unsupported_or_needs_manual_review": False,
            "unsupported_reasons": [],
            "effect_summary": "",
            "legacy_behavior_checklist": [],
            "candidate_ops_sequence": [],
            "test_ideas": [],
            "risk_notes": [],
            "must_not_emit_final_json": True,
            "error": "prompt_text 缺失，无法生成 draft preview",
        }

    # 检查是否有错误
    if source.get("error"):
        return {
            "meta": meta,
            "card_key": card_key,
            "draft_ready": False,
            "unsupported_or_needs_manual_review": True,
            "unsupported_reasons": [source["error"]],
            "effect_summary": "",
            "legacy_behavior_checklist": [],
            "candidate_ops_sequence": [],
            "test_ideas": [],
            "risk_notes": [],
            "must_not_emit_final_json": True,
            "error": source["error"],
        }

    # 检查 unsupported 配置（精确 card_key 优先）
    if card_key in _UNSUPPORTED_CONFIG:
        config = _UNSUPPORTED_CONFIG[card_key]
        return {
            "meta": meta,
            "card_key": card_key,
            "draft_ready": False,
            "unsupported_or_needs_manual_review": True,
            "unsupported_reasons": [config["label"]],
            "effect_summary": f"{config['name']} - 当前 runtime 不支持（{', '.join(config['reasons'])}）",
            "legacy_behavior_checklist": [],
            "candidate_ops_sequence": [],
            "test_ideas": [],
            "risk_notes": [
                f"需要 runtime 支持: {', '.join(config['reasons'])}",
            ],
            "must_not_emit_final_json": True,
        }

    # 匹配启发式
    heuristic = _match_card_heuristic(prompt_text, card_key)

    if heuristic is None:
        # 无法匹配任何启发式
        # 检查 unsupported_or_needs_manual_review 标记
        if source.get("unsupported_or_needs_manual_review"):
            return {
                "meta": meta,
                "card_key": card_key,
                "draft_ready": False,
                "unsupported_or_needs_manual_review": True,
                "unsupported_reasons": source.get("unsupported_reasons", []),
                "effect_summary": "",
                "legacy_behavior_checklist": [],
                "candidate_ops_sequence": [],
                "test_ideas": [],
                "risk_notes": [],
                "must_not_emit_final_json": True,
                "error": "无法匹配启发式规则且 prompt preview 标记为 unsupported",
            }
        else:
            return {
                "meta": meta,
                "card_key": card_key,
                "draft_ready": False,
                "unsupported_or_needs_manual_review": True,
                "unsupported_reasons": ["no_heuristic_match"],
                "effect_summary": "",
                "legacy_behavior_checklist": [],
                "candidate_ops_sequence": [],
                "test_ideas": [],
                "risk_notes": [],
                "must_not_emit_final_json": True,
                "error": "无法匹配启发式规则",
            }

    # 生成 candidate ops
    if heuristic == "professors_research":
        candidate_ops = _build_professors_research_ops()
        effect_summary = (
            "将自己的手牌全部丢弃，然后抽 7 张牌，并标记本回合已使用支援者。"
        )
        risk_notes: list[str] = []
    elif heuristic == "carmine":
        candidate_ops = _build_carmine_ops()
        effect_summary = (
            "将自己的手牌全部丢弃，然后抽 5 张牌，并标记本回合已使用支援者。"
        )
        risk_notes = []
        if _detect_any_keyword(prompt_text, _FIRST_TURN_KEYWORDS):
            risk_notes.append(
                "usable_on_first_turn_if_going_first: "
                "先攻玩家的最初回合也可以使用（playability condition，不属于 effect resolve_ops）"
            )
        else:
            # 对于 TWM-145 卡牌 key 已知时也加这个注释
            risk_notes.append(
                "special_notes: TWM-145 Carmine 在先攻玩家的最初回合也可以使用"
            )
    else:
        candidate_ops = []
        effect_summary = ""

    # 检查 unsupported_or_needs_manual_review
    needs_review = source.get("unsupported_or_needs_manual_review", False)
    unsupported_reasons = list(source.get("unsupported_reasons", []))

    # 如果 strict 模式，验证需要的 op 都在支持列表中
    if strict_supported_ops and candidate_ops:
        for op in candidate_ops:
            if op["op_type"] not in _SUPPORTED_OPS:
                return {
                    "meta": meta,
                    "card_key": card_key,
                    "draft_ready": False,
                    "unsupported_or_needs_manual_review": True,
                    "unsupported_reasons": [
                        f"op_type '{op['op_type']}' 不在当前 runtime 支持列表中"
                    ],
                    "effect_summary": effect_summary,
                    "legacy_behavior_checklist": [],
                    "candidate_ops_sequence": [],
                    "test_ideas": [],
                    "risk_notes": risk_notes,
                    "must_not_emit_final_json": True,
                }

    return {
        "meta": meta,
        "card_key": card_key,
        "draft_ready": True,
        "unsupported_or_needs_manual_review": needs_review,
        "unsupported_reasons": unsupported_reasons,
        "effect_summary": effect_summary,
        "legacy_behavior_checklist": [
            "supporterPlayedTurn 标记",
            "卡牌自身从 hand 移动到 discard",
            "全部手牌弃置到 discard",
            "从牌库上方抽指定数量",
        ],
        "candidate_ops_sequence": candidate_ops,
        "test_ideas": [
            "侧信道测试：验证 resolve_ops 返回与 draft 一致",
            "侧信道测试：验证桥接器执行后 hand/discard/left 区域正确",
        ],
        "risk_notes": risk_notes,
        "must_not_emit_final_json": True,
    }
