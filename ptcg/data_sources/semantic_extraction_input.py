"""语义提取输入包 preview —— 纯函数，不联网，不调用 LLM。

从 application preview JSON 构建面向 semantic extraction prompt 的
结构化输入包。不生成 semantic ops JSON，不生成最终 prompt。
"""

from __future__ import annotations

import copy
from typing import Any

# ---------------------------------------------------------------------------
# 当前运行时支持的 semantic op 清单
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
# 危险输出路径名单
# ---------------------------------------------------------------------------

_FORBIDDEN_OUTPUT_NAMES: set[str] = {
    "card_chinese_data.json",
    "card_data_cache.json",
    "normalized_card_text.json",
}

_FORBIDDEN_ENDS_WITH: tuple[str, ...] = (
    "semantic_ops.json",
)

_FORBIDDEN_CONTAINS: tuple[tuple[str, tuple[str, ...]], ...] = (
    # (substring, extensions)
    ("prompt", (".md", ".txt", ".json")),
)


def _is_dangerous_output_path(path: str) -> str | None:
    """检查输出路径是否危险。返回错误消息或 None（安全）。"""
    import os

    name = os.path.basename(path)

    # 完全匹配禁止列表
    if name in _FORBIDDEN_OUTPUT_NAMES:
        return f"禁止写入受保护的文件: {name}"

    # data/normalized_card_text.json
    if path.replace("\\", "/").startswith("data/") and name == "normalized_card_text.json":
        return f"禁止写入 data/normalized_card_text.json"

    # 任意 normalized_card_text.json
    if "normalized_card_text.json" in path:
        return f"禁止写入任何 normalized_card_text.json 文件: {path}"

    # 以 semantic_ops.json 结尾
    if name.endswith(_FORBIDDEN_ENDS_WITH):
        return f"禁止写入 semantic_ops.json: {path}"

    # 包含 prompt 且扩展名为 .md/.txt/.json
    for substr, extensions in _FORBIDDEN_CONTAINS:
        if substr in name.lower():
            _, ext = os.path.splitext(name)
            if ext.lower() in extensions:
                return f"禁止写入 prompt 相关文件: {path}"

    return None


# ---------------------------------------------------------------------------
# 核心构建函数
# ---------------------------------------------------------------------------


def build_semantic_extraction_input_preview(
    application_preview: dict,
    *,
    card_keys: list[str] | None = None,
    limit: int | None = None,
    include_op_inventory: bool = True,
    fail_on_not_ready: bool = False,
) -> dict:
    """从 application preview 构建语义提取输入包 preview。

    Args:
        application_preview: apply_refetch_preview.py 输出的 application preview JSON。
        card_keys: 只处理指定 card_key 列表。None 表示全部。
        limit: 最多处理 N 张卡。None 表示不限制。
        include_op_inventory: 是否包含当前支持的 op 清单。
        fail_on_not_ready: 若选中的卡中存在不满足 prompt_ready 的，在返回的
            meta 中标记并让调用方决定是否失败。

    Returns:
        semantic extraction input preview dict。
    """
    # deep copy 输入，防止副作用
    source = copy.deepcopy(application_preview)

    applications = source.get("applications", [])

    # 按 card_key 过滤
    if card_keys:
        key_set = set(card_keys)
        candidates = [a for a in applications if a.get("card_key") in key_set]
    else:
        candidates = list(applications)

    # 区分 ready / not ready
    ready: list[dict] = []
    not_ready: list[dict] = []

    for app in candidates:
        record = app.get("updated_record_preview", {})
        flags = record.get("quality_flags", {})
        is_applied = bool(app.get("applied"))

        if is_applied and flags.get("prompt_ready") is True:
            ready.append(app)
        else:
            not_ready.append(app)

    not_ready_count = len(not_ready)

    # 只取 ready 的卡
    selected = ready[:limit] if limit is not None else ready

    # 组装输出
    cards_output: list[dict] = []
    for app in selected:
        card_key = app.get("card_key", "???")
        record = app.get("updated_record_preview", {})
        identity = record.get("identity", {})
        classification = record.get("classification", {})
        text_block = record.get("text", {})
        flags = record.get("quality_flags", {})
        provenance = record.get("provenance", {})
        report = app.get("application_report", {})

        # 提取 identity 关键字段
        identity_out = {
            "card_key": card_key,
            "name_en": identity.get("name_en"),
            "name_zh": identity.get("name_zh"),
            "set_code": identity.get("set_code"),
            "number": identity.get("number"),
        }

        # 提取 classification 关键字段
        classification_out = {
            "card_supertype": classification.get("card_supertype"),
            "trainer_subtype": classification.get("trainer_subtype"),
            "classification_source": classification.get("classification_source"),
            "classification_confidence": classification.get("classification_confidence"),
        }

        # 提取文本
        normalized_text = {
            "rules_text_zh": text_block.get("rules_text_zh"),
            "trainer_text_zh": text_block.get("trainer_text_zh"),
            "full_text_zh": text_block.get("full_text_zh"),
        }

        # 提取 provenance 摘要
        provenance_summary = {
            "field_source_map_keys": sorted(
                provenance.get("field_source_map", {}).keys()
            ),
            "sources": [
                {
                    "id": s.get("id"),
                    "type": s.get("type"),
                }
                for s in provenance.get("sources", [])
            ],
        }
        refetch = provenance.get("refetch", {})
        if refetch:
            provenance_summary["refetch_source"] = refetch.get("source")
            provenance_summary["refetch_response_shape"] = refetch.get("response_shape")

        # 提取 application 摘要
        application_summary = {
            "applied_fields": list(report.get("applied_fields", [])),
            "skipped_fields": list(report.get("skipped_fields", [])),
            "warnings": list(report.get("warnings", [])),
            "errors": list(report.get("errors", [])),
        }

        # 局部文件路径
        local_file = identity.get("local_file")

        cards_output.append({
            "card_key": card_key,
            "identity": identity_out,
            "classification": classification_out,
            "local_file": local_file,
            "normalized_text": normalized_text,
            "quality_flags": flags,
            "provenance_summary": provenance_summary,
            "application_summary": application_summary,
            "semantic_extraction_task": {
                "task_type": "supporter_effect_to_semantic_ops",
                "expected_output_kind": "semantic_ops_draft",
                "must_not_emit_final_json": True,
                "must_preserve_legacy_behavior": True,
            },
            "known_runtime_support": {
                "available_ops": list(_SUPPORTED_OPS),
            },
        })

    result: dict[str, Any] = {
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
            "input_application_count": len(candidates),
            "selected_count": len(selected),
            "ready_count": len(ready),
            "not_ready_count": not_ready_count,
            "error_count": 0,
            "warning_count": 0,
        },
    }

    if include_op_inventory:
        result["op_inventory"] = {
            "allowed_ops": list(_SUPPORTED_OPS),
            "disallowed_patterns": list(_DISALLOWED_PATTERNS),
        }

    result["cards"] = cards_output

    # fail_on_not_ready 标记
    if fail_on_not_ready and not_ready_count > 0:
        result["meta"]["fail_on_not_ready_triggered"] = True

    return result
