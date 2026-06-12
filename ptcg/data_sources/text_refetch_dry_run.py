"""Build dry-run requests for targeted text refetch without network access.

Consumes Phase 7E refetch plan items and produces structured dry-run
request dictionaries that describe how each card would be fetched from
tcg.mik.moe in a future real-fetch pass.
"""

from __future__ import annotations

from typing import Any

_SOURCE_NAME = "tcg.mik.moe card-detail"

_FIELD_MAPPING_TRAINER = {
    "description": [
        "text.rules_text_zh",
        "text.trainer_text_zh",
        "text.full_text_zh",
    ],
    "cardType": [
        "classification.card_supertype",
        "classification.trainer_subtype",
    ],
}

_FIELD_MAPPING_POKEMON_ATTACKS = {
    "pokemonAttr.attack[].text": ["attacks[].effect_text_zh"],
}

_FIELD_MAPPING_POKEMON_ABILITIES = {
    "pokemonAttr.ability[].text": ["abilities[].effect_text_zh"],
}


def _has_mik_ids(source_ids: dict[str, Any]) -> bool:
    return bool(
        source_ids.get("set_code_cn") and source_ids.get("card_index_cn")
    )


def _derive_lookup_strategy(plan_item: dict[str, Any]) -> tuple[str, dict[str, Any], list[str]]:
    source_ids: dict[str, Any] = plan_item.get("source_ids", {})
    notes: list[str] = []

    if _has_mik_ids(source_ids):
        strategy = "detail_by_source_ids"
    elif source_ids.get("card_data_cache_key"):
        parts = (source_ids.get("card_data_cache_key") or "").split("-")
        if len(parts) >= 2:
            strategy = "search_then_detail_by_set_number"
            notes.append("needs_lookup_before_detail")
        else:
            strategy = "search_then_detail_by_name"
            notes.append("name_lookup_may_be_ambiguous")
    else:
        strategy = "unavailable"

    lookup: dict[str, Any] = {
        "set_code_cn": source_ids.get("set_code_cn"),
        "card_index_cn": source_ids.get("card_index_cn"),
        "name_en": plan_item.get("name_en"),
        "name_zh": plan_item.get("name_zh"),
    }
    return strategy, lookup, notes


def _build_field_mapping(desired_fields: list[str]) -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = {}

    has_text = bool(
        {"rules_text_zh", "trainer_text_zh", "full_text_zh"} & set(desired_fields)
    )
    has_type = bool(
        {"card_supertype", "trainer_subtype"} & set(desired_fields)
    )
    has_attack_effect = "attacks[].effect_text_zh" in desired_fields
    has_ability_effect = "abilities[].effect_text_zh" in desired_fields

    if has_text or has_type:
        if has_text:
            mapping.setdefault("description", []).extend(
                _FIELD_MAPPING_TRAINER["description"]
            )
        if has_type:
            mapping.setdefault("cardType", []).extend(
                _FIELD_MAPPING_TRAINER["cardType"]
            )

    if has_attack_effect:
        mapping.setdefault("pokemonAttr.attack[].text", []).extend(
            _FIELD_MAPPING_POKEMON_ATTACKS["pokemonAttr.attack[].text"]
        )

    if has_ability_effect:
        mapping.setdefault("pokemonAttr.ability[].text", []).extend(
            _FIELD_MAPPING_POKEMON_ABILITIES["pokemonAttr.ability[].text"]
        )

    return mapping


def _derive_expected_source_fields(field_mapping: dict[str, list[str]]) -> list[str]:
    return list(field_mapping)


def build_refetch_dry_run_requests(plan_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert Phase 7E plan items into dry-run request dicts.

    Each returned dict describes *what would be done* in a future real
    fetch pass, without performing any network I/O or file writes.
    """
    requests: list[dict[str, Any]] = []
    for item in plan_items:
        desired_fields: list[str] = list(item.get("desired_fields", []))
        field_mapping = _build_field_mapping(desired_fields)
        card_can_refetch: bool = item.get("can_refetch", False)
        blocking_issues: list[str] = list(item.get("blocking_issues", []))

        strategy, lookup, notes = _derive_lookup_strategy(item)

        if strategy == "unavailable":
            can_refetch = False
            if "missing_refetch_locator" not in blocking_issues:
                blocking_issues.append("missing_refetch_locator")
        else:
            can_refetch = card_can_refetch

        requests.append(
            {
                "card_key": item.get("card_key"),
                "name_en": item.get("name_en"),
                "name_zh": item.get("name_zh"),
                "can_refetch": can_refetch,
                "method": "GET",
                "source": _SOURCE_NAME,
                "lookup_strategy": strategy,
                "lookup": lookup,
                "expected_source_fields": _derive_expected_source_fields(field_mapping),
                "field_mapping": field_mapping,
                "desired_fields": desired_fields,
                "dry_run": True,
                "will_write_files": False,
                "network_enabled": False,
                "blocking_issues": blocking_issues,
                "notes": notes,
            }
        )
    return requests


__all__ = ["build_refetch_dry_run_requests"]
