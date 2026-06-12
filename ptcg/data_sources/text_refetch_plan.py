"""Build dry-run plans for future targeted text refetch work."""

from __future__ import annotations

from typing import Any


_DETAIL_SOURCE_NAME = "tcg.mik.moe card-detail"
_DETAIL_LOCATOR_KEY_SETS = (
    ("mik_set_code", "mik_card_index"),
    ("set_code_cn", "card_index_cn"),
)
_PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2}
_SUPERTYPE_ORDER = {"Trainer": 0, "Pokemon": 1, "Energy": 2, "Unknown": 3}
_TRAINER_SUBTYPES = {"Supporter", "Item", "Stadium", "Tool"}


def _is_trainer_like(classification: dict[str, Any]) -> bool:
    return classification.get("card_supertype") == "Trainer" or (
        classification.get("trainer_subtype") in _TRAINER_SUBTYPES
    )


def _derive_priority(
    card_key: str,
    identity: dict[str, Any],
    classification: dict[str, Any],
    quality_flags: dict[str, Any],
    text: dict[str, Any],
    priority_card_keys: set[str],
) -> str | None:
    if card_key in priority_card_keys:
        return "P0"

    if _is_trainer_like(classification) and quality_flags.get("missing_rules_text"):
        return "P0"

    if (
        not quality_flags.get("prompt_ready", False)
        and quality_flags.get("needs_text_refetch")
        and identity.get("local_file")
    ):
        return "P0"

    if (
        classification.get("card_supertype") == "Pokemon"
        and quality_flags.get("missing_effect_text")
    ):
        return "P1"

    if quality_flags.get("untrusted_card_type") and quality_flags.get("needs_type_refetch"):
        return "P1"

    if text.get("text_quality") == "partial" or quality_flags.get("derived_from_partial_sources"):
        return "P2"

    return None


def _derive_reasons(
    card_key: str,
    quality_flags: dict[str, Any],
    priority_card_keys: set[str],
) -> list[str]:
    reasons: list[str] = []

    if card_key in priority_card_keys:
        reasons.append("priority_card_key")
    if quality_flags.get("missing_rules_text"):
        reasons.append("missing_rules_text")
    if quality_flags.get("missing_effect_text"):
        reasons.append("missing_effect_text")
    if quality_flags.get("needs_text_refetch"):
        reasons.append("needs_text_refetch")
    if quality_flags.get("needs_type_refetch"):
        reasons.append("needs_type_refetch")
    if quality_flags.get("untrusted_card_type"):
        reasons.append("untrusted_card_type")
    if quality_flags.get("missing_local_file"):
        reasons.append("missing_local_file")
    if quality_flags.get("ambiguous_mapping"):
        reasons.append("ambiguous_mapping")
    if quality_flags.get("derived_from_partial_sources"):
        reasons.append("derived_from_partial_sources")
    if not quality_flags.get("prompt_ready", False):
        reasons.append("prompt_not_ready")

    return reasons


def _append_unique(items: list[str], *values: str) -> None:
    for value in values:
        if value not in items:
            items.append(value)


def _derive_desired_fields(
    classification: dict[str, Any],
    quality_flags: dict[str, Any],
    text: dict[str, Any],
) -> list[str]:
    desired_fields: list[str] = []

    if _is_trainer_like(classification) and quality_flags.get("missing_rules_text"):
        _append_unique(
            desired_fields,
            "rules_text_zh",
            "trainer_text_zh",
            "full_text_zh",
            "card_supertype",
            "trainer_subtype",
        )

    if (
        classification.get("card_supertype") == "Pokemon"
        and quality_flags.get("missing_effect_text")
    ):
        _append_unique(
            desired_fields,
            "attacks[].effect_text_zh",
            "abilities[].effect_text_zh",
            "full_text_zh",
        )

    if quality_flags.get("needs_type_refetch"):
        _append_unique(
            desired_fields,
            "card_supertype",
            "trainer_subtype",
            "pokemon_stage",
            "energy_type",
        )

    if text.get("text_quality") == "partial" or quality_flags.get("derived_from_partial_sources"):
        _append_unique(desired_fields, "full_text_zh")

    if quality_flags.get("needs_text_refetch") and not desired_fields:
        _append_unique(desired_fields, "full_text_zh")

    return desired_fields


def _derive_suggested_source(desired_fields: list[str]) -> dict[str, Any]:
    source_fields: list[str] = []

    if any(
        field in desired_fields
        for field in ("rules_text_zh", "trainer_text_zh", "full_text_zh")
    ):
        _append_unique(source_fields, "description")

    if any(
        field in desired_fields
        for field in ("card_supertype", "trainer_subtype", "pokemon_stage", "energy_type")
    ):
        _append_unique(source_fields, "cardType")

    if "attacks[].effect_text_zh" in desired_fields:
        _append_unique(source_fields, "pokemonAttr.attack[].text")

    if "abilities[].effect_text_zh" in desired_fields:
        _append_unique(source_fields, "pokemonAttr.ability[].text")

    return {
        "name": _DETAIL_SOURCE_NAME,
        "fields": source_fields,
    }


def _has_detail_locator(source_ids: dict[str, Any]) -> bool:
    return any(all(source_ids.get(key) for key in keys) for keys in _DETAIL_LOCATOR_KEY_SETS)


def _has_lookup_locator(identity: dict[str, Any]) -> bool:
    return bool(
        identity.get("set_code")
        and identity.get("normalized_number")
        and (identity.get("name_en") or identity.get("name_zh"))
    )


def _derive_refetchability(
    identity: dict[str, Any],
    reasons: list[str],
) -> tuple[bool, list[str]]:
    source_ids = identity.get("source_ids") or {}
    blocking_issues: list[str] = []

    if _has_detail_locator(source_ids):
        return True, blocking_issues

    if _has_lookup_locator(identity):
        if "needs_lookup_before_detail" not in reasons:
            reasons.append("needs_lookup_before_detail")
        return True, blocking_issues

    blocking_issues.append("missing_refetch_locator")
    return False, blocking_issues


def build_text_refetch_plan(
    normalized_records: dict[str, dict[str, Any]],
    priority_card_keys: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Build a stable dry-run plan for targeted text refetch."""
    priority_card_keys = priority_card_keys or set()
    plan: list[dict[str, Any]] = []

    for card_key, record in normalized_records.items():
        identity = record.get("identity") or {}
        classification = record.get("classification") or {}
        quality_flags = record.get("quality_flags") or {}
        text = record.get("text") or {}

        if (
            quality_flags.get("prompt_ready")
            and not quality_flags.get("needs_text_refetch")
            and not quality_flags.get("needs_type_refetch")
        ):
            continue

        priority = _derive_priority(
            card_key=card_key,
            identity=identity,
            classification=classification,
            quality_flags=quality_flags,
            text=text,
            priority_card_keys=priority_card_keys,
        )

        if priority is None and not quality_flags.get("missing_local_file"):
            continue

        reasons = _derive_reasons(card_key, quality_flags, priority_card_keys)
        desired_fields = _derive_desired_fields(classification, quality_flags, text)
        can_refetch, blocking_issues = _derive_refetchability(identity, reasons)
        plan.append(
            {
                "card_key": card_key,
                "name_en": identity.get("name_en"),
                "name_zh": identity.get("name_zh"),
                "local_file": identity.get("local_file"),
                "card_supertype": classification.get("card_supertype", "Unknown"),
                "trainer_subtype": classification.get("trainer_subtype", "Unknown"),
                "priority": priority or "P2",
                "reasons": reasons,
                "desired_fields": desired_fields,
                "suggested_source": _derive_suggested_source(desired_fields),
                "source_ids": dict(identity.get("source_ids") or {}),
                "can_refetch": can_refetch,
                "blocking_issues": blocking_issues,
                "dry_run": True,
            }
        )

    plan.sort(
        key=lambda item: (
            _PRIORITY_ORDER.get(item["priority"], 99),
            _SUPERTYPE_ORDER.get(item["card_supertype"], 99),
            item["card_key"],
        )
    )
    return plan


__all__ = ["build_text_refetch_plan"]
