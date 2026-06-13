"""单卡 semantic extraction prompt preview —— 纯函数，不联网，不调用 LLM。

从 semantic extraction input preview JSON 中提取指定 card_key 的数据，
生成面向 LLM 的 prompt preview。不生成 semantic ops JSON，不生成最终 prompt。
"""

from __future__ import annotations

import copy
from typing import Any

# ---------------------------------------------------------------------------
# 当前支持的 semantic op 清单
# ---------------------------------------------------------------------------

_SUPPORTED_OPS = [
    "move_cards",
    "discard_cards",
    "draw_cards",
    "mark_supporter_played",
]

_DISALLOWED_PATTERNS = [
    "choice",
    "optional",
    "conditional branch",
    "search deck",
    "shuffle random hidden zone unless explicitly supported",
    "generic set_attr",
]

# ---------------------------------------------------------------------------
# 简单中文关键词检测（unsupported pattern）
# ---------------------------------------------------------------------------

_UNSUPPORTED_KEYWORDS: dict[str, str] = {
    "选择": "choice / 选择类操作当前 runtime 不支持",
    "可以": "optional / 可选条件分支当前 runtime 不支持",
    "从牌库选择": "search deck / 牌库搜索当前 runtime 不支持",
    "查看牌库": "search deck / 查看牌库当前 runtime 不支持",
    "随机": "random / 随机性操作当前 runtime 不支持",
    "从弃牌区选择": "choice from discard / 从弃牌区选择当前 runtime 不支持",
}


def _detect_unsupported_patterns(text: str) -> list[str]:
    """基于简单关键词检测不支持的模式。"""
    reasons: list[str] = []
    for keyword, reason in _UNSUPPORTED_KEYWORDS.items():
        if keyword in text:
            reasons.append(f"{keyword}: {reason}")
    return reasons


# ---------------------------------------------------------------------------
# prompt 构建
# ---------------------------------------------------------------------------


def _build_prompt_text(
    card: dict[str, Any],
    include_legacy_context: bool,
    include_op_inventory: bool,
    unsupported_reasons: list[str],
) -> str:
    """构建中文 prompt_text。"""
    identity = card.get("identity", {})
    classification = card.get("classification", {})
    text = card.get("normalized_text", {})
    local_file = card.get("local_file", "")

    name_zh = identity.get("name_zh", "???")
    name_en = identity.get("name_en", "???")
    card_key = card.get("card_key", "???")
    set_code = identity.get("set_code", "")
    number = identity.get("number", "")

    rules = text.get("rules_text_zh") or ""
    trainer = text.get("trainer_text_zh") or ""
    full_text = text.get("full_text_zh") or ""
    display_text = full_text or trainer or rules

    parts: list[str] = []

    # 任务
    parts.append("## 任务")
    parts.append("")
    parts.append(
        "根据以下卡牌的中文效果文本，提出 semantic ops 草稿（不输出最终 JSON）。"
    )
    parts.append("")

    # 卡牌信息
    parts.append("## 卡牌信息")
    parts.append("")
    parts.append(f"- card_key: {card_key}")
    parts.append(f"- 英文名: {name_en}")
    parts.append(f"- 中文名: {name_zh}")
    parts.append(f"- set / number: {set_code} / {number}")
    parts.append(f"- card_supertype: {classification.get('card_supertype', '???')}")
    parts.append(f"- trainer_subtype: {classification.get('trainer_subtype', '???')}")

    if include_legacy_context and local_file:
        parts.append(f"- 本地 legacy 实现: {local_file}")

    parts.append("")
    parts.append("### 中文效果文本")
    parts.append("")
    parts.append(display_text)
    parts.append("")

    # legacy 上下文
    if include_legacy_context:
        parts.append("## Legacy 行为约束")
        parts.append("")
        parts.append("必须保留本地 legacy reduce_action 的行为语义，包括：")
        parts.append("")
        parts.append("- supporterPlayedTurn 标记逻辑")
        parts.append("- 卡牌移动/弃置/抽牌的执行顺序")
        parts.append("- 边界条件（如牌库不足、手牌为空等）")
        parts.append("")

    # 当前 runtime 支持
    if include_op_inventory:
        parts.append("## 当前 runtime 支持")
        parts.append("")
        parts.append("只能使用以下 op：")
        parts.append("")
        for op in _SUPPORTED_OPS:
            parts.append(f"- {op}")
        parts.append("")

    # 禁止事项
    parts.append("## 禁止事项")
    parts.append("")
    parts.append("明确禁止以下行为：")
    parts.append("")
    parts.append("- 输出最终 semantic ops JSON")
    parts.append("- 直接修改代码（ptcg/cards/、ptcg/core/ 等）")
    parts.append("- 发明 runtime 不支持的 op")
    parts.append("- 使用 generic set_attr")
    parts.append("- 使用 choice / optional / conditional branch，除非后续 runtime 支持")
    parts.append("- 忽略 legacy behavior")
    parts.append("- 忽略 supporterPlayedTurn 标记")
    parts.append("")

    # unsupported 检测
    if unsupported_reasons:
        parts.append("## 不支持模式警告")
        parts.append("")
        parts.append("以下模式当前 runtime 不支持，生成草稿时需标记为 manual_review：")
        parts.append("")
        for reason in unsupported_reasons:
            parts.append(f"- {reason}")
        parts.append("")

    # 预期输出
    parts.append("## 预期输出（仅草稿分析）")
    parts.append("")
    parts.append("请输出以下结构化的草稿分析：")
    parts.append("")
    parts.append("1. **effect summary**: 用中文简述卡牌效果")
    parts.append("2. **legacy behavior checklist**: 逐项对比 legacy 行为")
    parts.append("3. **candidate ops sequence**: 建议的 semantic op 序列")
    parts.append("   - 每个 op 标注 type / category / actor / order / source / target / params")
    parts.append("4. **unsupported requirements**: 需要 runtime 扩展才能支持的部分")
    parts.append("5. **test ideas**: 侧信道测试建议")
    parts.append("6. **risk notes**: 潜在风险（边界条件、与 legacy 差异等）")
    parts.append("")

    # 审查清单
    parts.append("## 审查清单（生成后检查）")
    parts.append("")
    parts.append("- [ ] 是否移动自身卡牌到弃牌区（move_cards self）")
    parts.append("- [ ] 是否弃掉手牌（discard_cards from hand to discard）")
    parts.append("- [ ] 是否抽牌数量正确（draw_cards count=N）")
    parts.append("- [ ] 是否标记 supporter played（mark_supporter_played）")
    parts.append("- [ ] 是否和 legacy reduce_action 行为一致")
    parts.append("- [ ] 是否需要 unsupported runtime feature")
    parts.append("")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# 核心构建函数
# ---------------------------------------------------------------------------


def build_semantic_extraction_prompt_preview(
    semantic_input_preview: dict,
    *,
    card_key: str,
    include_legacy_context: bool = True,
    include_op_inventory: bool = True,
) -> dict:
    """从 semantic extraction input preview 生成单卡 prompt preview。

    Args:
        semantic_input_preview: build_semantic_extraction_input.py 输出的
            semantic extraction input preview JSON。
        card_key: 目标卡牌 key。
        include_legacy_context: 是否包含 legacy 文件路径和行为约束。
        include_op_inventory: 是否包含当前 runtime 支持的 op 清单。

    Returns:
        prompt preview dict。
    """
    source = copy.deepcopy(semantic_input_preview)

    cards = source.get("cards", [])
    target_card: dict[str, Any] | None = None
    for c in cards:
        if c.get("card_key") == card_key:
            target_card = c
            break

    if target_card is None:
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
            "prompt_ready": False,
            "error": f"card_key '{card_key}' not found in input preview",
            "unsupported_or_needs_manual_review": False,
            "unsupported_reasons": [],
            "prompt_preview": {},
        }

    flags = target_card.get("quality_flags", {})
    prompt_ready = flags.get("prompt_ready", False)

    # 检测不支持的模式
    text = target_card.get("normalized_text", {})
    full_text = text.get("full_text_zh") or text.get("trainer_text_zh") or text.get("rules_text_zh") or ""
    unsupported_reasons = _detect_unsupported_patterns(full_text)
    needs_review = len(unsupported_reasons) > 0

    # 构建 prompt_text
    prompt_text = _build_prompt_text(
        target_card,
        include_legacy_context=include_legacy_context,
        include_op_inventory=include_op_inventory,
        unsupported_reasons=unsupported_reasons,
    )

    # system constraints
    system_constraints = [
        "不得生成最终 semantic ops JSON",
        "不得修改 ptcg/cards/ 或 ptcg/core/",
        "只能使用 runtime 支持的 op: " + ", ".join(_SUPPORTED_OPS),
        "必须保留 legacy reduce_action 行为语义",
    ]

    if unsupported_reasons:
        system_constraints.append(
            "存在 unsupported patterns，需在 analysis 中标记 manual_review"
        )

    # review checklist
    review_checklist = [
        "move_cards: 是否将自身卡牌从 hand 移动到 discard",
        "discard_cards: 是否丢弃手牌所有卡 (count=all)",
        "draw_cards: 抽牌数量是否正确 (count=N)",
        "mark_supporter_played: 是否标记 supporterPlayedTurn",
        "legacy_consistency: 是否与 legacy reduce_action 行为一致",
    ]

    if unsupported_reasons:
        for reason in unsupported_reasons:
            review_checklist.append(f"manual_review: {reason}")

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
        "unsupported_or_needs_manual_review": needs_review,
        "unsupported_reasons": unsupported_reasons,
        "prompt_preview": {
            "language": "zh",
            "purpose": (
                "根据 normalized 中文卡牌文本生成 semantic ops 草稿，"
                "不输出最终 JSON"
            ),
            "system_constraints": system_constraints,
            "card_context": {
                "card_key": target_card.get("card_key"),
                "name_en": target_card.get("identity", {}).get("name_en"),
                "name_zh": target_card.get("identity", {}).get("name_zh"),
                "local_file": target_card.get("local_file"),
                "classification": target_card.get("classification"),
            },
            "available_ops": list(_SUPPORTED_OPS),
            "disallowed_patterns": list(_DISALLOWED_PATTERNS),
            "required_output_shape": {
                "effect_summary": "中文简述卡牌效果",
                "legacy_behavior_checklist": "逐项对比 legacy 行为",
                "candidate_ops_sequence": "建议的 semantic op 序列",
                "unsupported_requirements": "需要 runtime 扩展才能支持的部分",
                "test_ideas": "侧信道测试建议",
                "risk_notes": "潜在风险（边界条件、与 legacy 差异等）",
            },
            "review_checklist": review_checklist,
            "prompt_text": prompt_text,
        },
    }
