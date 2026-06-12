"""Build normalized card text records from local caches without network access."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.0"
GENERATOR_VERSION = "0.1.0"
_FORBIDDEN_IMPORTS = {"requests", "httpx", "aiohttp", "bs4"}
_TRAINER_BASES = {
    "SupporterCard": "Supporter",
    "ItemCard": "Item",
    "StadiumCard": "Stadium",
    "ToolCard": "Tool",
}
_UNKNOWN_TEXT = {
    "rules_text_zh": None,
    "rules_text_en": None,
    "trainer_text_zh": None,
    "trainer_text_en": None,
    "full_text_zh": None,
    "full_text_en": None,
    "text_available": False,
    "text_quality": "missing",
}


def normalize_number(number: str | int | None) -> str:
    """Normalize card numbers for comparisons while preserving suffixes."""
    if number is None:
        return ""

    text = str(number).strip()
    if not text:
        return ""

    match = re.match(r"^0*(\d+)([A-Za-z].*)?$", text)
    if match:
        digits, suffix = match.groups()
        normalized_digits = digits.lstrip("0") or "0"
        return normalized_digits + (suffix or "")
    return text.upper()


def make_card_key(set_code: str | None, number: str | int | None) -> str:
    """Create the stable external card key using the original number shape."""
    left = (set_code or "").strip().upper()
    right = str(number or "").strip().upper()
    if not left:
        return right
    if not right:
        return left
    return f"{left}-{right}"


def load_card_chinese_data(path: Path) -> list[dict[str, Any]]:
    """Load Chinese card data records as a flat list."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    cards = payload.get("cards", {})
    records: list[dict[str, Any]] = []
    for source_key, record in cards.items():
        item = dict(record)
        item["_source_key"] = source_key
        records.append(item)
    return records


def load_card_data_cache(path: Path) -> dict[str, dict[str, Any]]:
    """Load card cache records keyed by `SET-NUMBER`."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {str(key): dict(value) for key, value in payload.items()}


def _expr_to_str(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _base_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def infer_local_card_class_info(file_path: Path) -> dict[str, Any]:
    """Infer class identity and inheritance info from a local card source file."""
    source = file_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    card_class: ast.ClassDef | None = None
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and any(
            _base_name(base) in _TRAINER_BASES
            or _base_name(base) in {"PokemonCard", "EnergyCard"}
            for base in node.bases
        ):
            card_class = node
            break

    if card_class is None:
        return {
            "class_name": None,
            "base_classes": [],
            "set_name": None,
            "number": None,
            "name": None,
            "card_supertype": "Unknown",
            "trainer_subtype": "Unknown",
            "classification_confidence": "low",
            "classification_source": None,
            "classification_warnings": ["local_class_not_found"],
        }

    base_classes = [name for base in card_class.bases if (name := _base_name(base))]
    assigned: dict[str, str] = {}
    for node in card_class.body:
        if isinstance(node, ast.FunctionDef) and node.name == "__init__":
            for stmt in ast.walk(node):
                if not isinstance(stmt, ast.Assign):
                    continue
                for target in stmt.targets:
                    if (
                        isinstance(target, ast.Attribute)
                        and isinstance(target.value, ast.Name)
                        and target.value.id == "self"
                    ):
                        value = _expr_to_str(stmt.value)
                        if value is not None:
                            assigned[target.attr] = value

    card_supertype = "Unknown"
    trainer_subtype = "Unknown"
    confidence = "high"
    source_name = "local_class"

    if "PokemonCard" in base_classes:
        card_supertype = "Pokemon"
    elif "EnergyCard" in base_classes:
        card_supertype = "Energy"
    else:
        for base_name, subtype in _TRAINER_BASES.items():
            if base_name in base_classes:
                card_supertype = "Trainer"
                trainer_subtype = subtype
                break

    return {
        "class_name": card_class.name,
        "base_classes": base_classes,
        "set_name": assigned.get("set_name"),
        "number": assigned.get("number"),
        "name": assigned.get("name"),
        "card_supertype": card_supertype,
        "trainer_subtype": trainer_subtype,
        "classification_confidence": confidence,
        "classification_source": source_name,
        "classification_warnings": [],
    }


def build_local_card_index(cards_root: Path) -> dict[str, Any]:
    """Index local card files by path and parseable filename key."""
    by_relative_path: dict[str, dict[str, Any]] = {}
    by_card_key: dict[str, list[dict[str, Any]]] = {}
    repo_root = cards_root.parent.parent

    for file_path in sorted(cards_root.rglob("*.py")):
        if file_path.name == "__init__.py":
            continue

        info = infer_local_card_class_info(file_path)
        relative_path = file_path.relative_to(repo_root).as_posix()
        info["relative_path"] = relative_path
        info["file_path"] = file_path
        by_relative_path[relative_path] = info

        match = re.match(r"^(?P<set>[A-Za-z]+)(?P<number>\d+)", file_path.stem)
        if not match:
            continue

        set_code = file_path.parent.name.upper()
        raw_number = match.group("number")
        parsed_key = f"{set_code}-{normalize_number(raw_number)}"
        by_card_key.setdefault(parsed_key, []).append(info)

    return {
        "by_relative_path": by_relative_path,
        "by_card_key": by_card_key,
    }


def _cache_key_from_record(record: dict[str, Any] | None) -> str | None:
    if not record:
        return None
    set_name = record.get("set_name")
    number = record.get("number")
    if not set_name or not number:
        return None
    return f"{str(set_name).upper()}-{normalize_number(number)}"


def _relative_card_path(raw_file: str | None) -> str | None:
    if not raw_file:
        return None
    cleaned = raw_file.replace("\\", "/").strip()
    if cleaned.startswith("ptcg/"):
        return cleaned
    if cleaned.startswith("cards/"):
        return f"ptcg/{cleaned}"
    return None


def _resolve_local_match(
    chinese_record: dict[str, Any] | None,
    cache_record: dict[str, Any] | None,
    local_index: dict[str, Any],
) -> tuple[dict[str, Any] | None, bool]:
    by_relative_path = local_index["by_relative_path"]
    by_card_key = local_index["by_card_key"]

    relative_file = _relative_card_path((chinese_record or {}).get("file"))
    if relative_file:
        return by_relative_path.get(relative_file), False

    fallback_key = _cache_key_from_record(chinese_record) or _cache_key_from_record(cache_record)
    if fallback_key:
        candidates = by_card_key.get(fallback_key, [])
        if len(candidates) == 1:
            return candidates[0], False
        if len(candidates) > 1:
            return None, True

    return None, False


def _build_sources(
    chinese_record: dict[str, Any] | None,
    cache_record: dict[str, Any] | None,
    local_match: dict[str, Any] | None,
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    sources: list[dict[str, Any]] = []
    field_source_map: dict[str, str] = {}

    if chinese_record:
        sources.append({"id": "card_chinese_data", "type": "json", "path": "card_chinese_data.json"})
    if cache_record:
        sources.append({"id": "card_data_cache", "type": "json", "path": "card_data_cache.json"})
    if local_match:
        sources.append(
            {
                "id": "local_class",
                "type": "python",
                "path": local_match["relative_path"],
            }
        )

    return sources, field_source_map


def _build_identity(
    card_key: str,
    chinese_record: dict[str, Any] | None,
    cache_record: dict[str, Any] | None,
    local_match: dict[str, Any] | None,
    field_source_map: dict[str, str],
) -> dict[str, Any]:
    primary = chinese_record or cache_record or {}
    set_code = str(primary.get("set_name") or "").upper() or None
    number = primary.get("number")
    normalized_number = normalize_number(number)
    name_en = primary.get("name")
    name_zh = (chinese_record or {}).get("chinese_name") or cache_record and cache_record.get("name")

    if name_en is not None:
        field_source_map["identity.name_en"] = "card_chinese_data" if chinese_record else "card_data_cache"
    if name_zh is not None:
        field_source_map["identity.name_zh"] = "card_chinese_data" if chinese_record else "card_data_cache"
    if local_match:
        field_source_map["identity.local_file"] = "local_class"
        field_source_map["identity.local_class_name"] = "local_class"

    source_ids: dict[str, Any] = {}
    if chinese_record:
        source_ids["card_chinese_key"] = chinese_record.get("_source_key")
        if chinese_record.get("set_code_cn"):
            source_ids["set_code_cn"] = chinese_record["set_code_cn"]
        if chinese_record.get("card_index_cn"):
            source_ids["card_index_cn"] = chinese_record["card_index_cn"]
    if cache_record:
        source_ids["card_data_cache_key"] = _cache_key_from_record(cache_record)

    return {
        "card_key": card_key,
        "set_code": set_code,
        "set_name": primary.get("set_name"),
        "number": number,
        "normalized_number": normalized_number,
        "name_en": name_en,
        "name_zh": name_zh,
        "local_file": local_match["relative_path"] if local_match else None,
        "local_class_name": local_match["class_name"] if local_match else None,
        "source_ids": source_ids,
    }


def _fallback_classification(cache_record: dict[str, Any] | None) -> tuple[dict[str, Any], bool, bool]:
    cache_type = (cache_record or {}).get("card_type")
    classification = {
        "card_supertype": "Unknown",
        "trainer_subtype": "Unknown",
        "pokemon_stage": None,
        "energy_type": None,
        "classification_confidence": "low",
        "classification_source": None,
        "classification_warnings": [],
    }

    if cache_type in {"Pokemon", "Trainer", "Energy"}:
        classification["card_supertype"] = cache_type
        classification["classification_source"] = "card_data_cache.card_type"
        classification["classification_warnings"] = ["card_data_cache.card_type_untrusted"]
        return classification, True, True

    classification["classification_warnings"] = ["classification_unknown"]
    return classification, False, True


def _build_classification(
    local_match: dict[str, Any] | None,
    cache_record: dict[str, Any] | None,
    field_source_map: dict[str, str],
) -> tuple[dict[str, Any], bool, bool]:
    cache_type = (cache_record or {}).get("card_type")
    if local_match and local_match.get("card_supertype") != "Unknown":
        classification = {
            "card_supertype": local_match["card_supertype"],
            "trainer_subtype": local_match["trainer_subtype"],
            "pokemon_stage": None,
            "energy_type": None,
            "classification_confidence": local_match["classification_confidence"],
            "classification_source": local_match["classification_source"],
            "classification_warnings": list(local_match["classification_warnings"]),
        }
        field_source_map["classification.card_supertype"] = "local_class"
        if classification["trainer_subtype"] != "Unknown":
            field_source_map["classification.trainer_subtype"] = "local_class"

        untrusted = False
        if cache_type and cache_type != classification["card_supertype"]:
            classification["classification_warnings"].append("card_type_conflict")
            classification["classification_warnings"].append("card_data_cache.card_type_untrusted")
            untrusted = True
        return classification, untrusted, False

    classification, untrusted, needs_refetch = _fallback_classification(cache_record)
    if classification["classification_source"]:
        field_source_map["classification.card_supertype"] = "card_data_cache"
    return classification, untrusted, needs_refetch


def _build_attacks(cache_record: dict[str, Any] | None) -> tuple[list[dict[str, Any]], bool]:
    if not cache_record:
        return [], True

    attacks = cache_record.get("attacks") or []
    attacks_en = cache_record.get("attacks_en") or []
    attacks_cn = cache_record.get("attacks_cn") or []
    normalized: list[dict[str, Any]] = []
    has_effect_text_zh = False

    for index, attack in enumerate(attacks):
        effect_text_zh = None
        if attack.get("effect_zh"):
            effect_text_zh = attack.get("effect_zh")
        elif attack.get("text_zh"):
            effect_text_zh = attack.get("text_zh")

        if effect_text_zh:
            has_effect_text_zh = True

        normalized.append(
            {
                "name_en": attacks_en[index] if index < len(attacks_en) else None,
                "name_zh": attacks_cn[index] if index < len(attacks_cn) else attack.get("name"),
                "cost": attack.get("cost"),
                "damage": attack.get("damage"),
                "effect_text_en": attack.get("effect_en") or attack.get("text_en"),
                "effect_text_zh": effect_text_zh,
                "source": "card_data_cache.attacks",
            }
        )
    return normalized, has_effect_text_zh


def _build_abilities(cache_record: dict[str, Any] | None) -> tuple[list[dict[str, Any]], bool]:
    if not cache_record:
        return [], True

    abilities = cache_record.get("abilities") or []
    abilities_en = cache_record.get("abilities_en") or []
    abilities_cn = cache_record.get("abilities_cn") or []
    normalized: list[dict[str, Any]] = []
    has_effect_text_zh = False

    for index, ability in enumerate(abilities):
        effect_text_zh = None
        if ability.get("effect_zh"):
            effect_text_zh = ability.get("effect_zh")
        elif ability.get("text_zh"):
            effect_text_zh = ability.get("text_zh")

        if effect_text_zh:
            has_effect_text_zh = True

        normalized.append(
            {
                "name_en": abilities_en[index] if index < len(abilities_en) else None,
                "name_zh": abilities_cn[index] if index < len(abilities_cn) else ability.get("name"),
                "ability_type": ability.get("type"),
                "effect_text_en": ability.get("effect_en") or ability.get("text_en"),
                "effect_text_zh": effect_text_zh,
                "source": "card_data_cache.abilities",
            }
        )
    return normalized, has_effect_text_zh


def _build_text(
    classification: dict[str, Any],
    has_effect_text_zh: bool,
) -> tuple[dict[str, Any], dict[str, bool]]:
    text = dict(_UNKNOWN_TEXT)
    supertype = classification["card_supertype"]
    trainer_subtype = classification["trainer_subtype"]

    missing_rules_text = False
    missing_effect_text = False
    needs_text_refetch = False
    unsupported_for_prompt = False
    prompt_ready = False

    is_trainer = supertype == "Trainer" or trainer_subtype != "Unknown"
    if is_trainer:
        missing_rules_text = True
        needs_text_refetch = True
        unsupported_for_prompt = True
    elif supertype == "Pokemon":
        missing_effect_text = not has_effect_text_zh
        needs_text_refetch = missing_effect_text
        unsupported_for_prompt = missing_effect_text
    elif supertype == "Energy":
        needs_text_refetch = True
        unsupported_for_prompt = True

    return text, {
        "missing_rules_text": missing_rules_text,
        "missing_effect_text": missing_effect_text,
        "needs_text_refetch": needs_text_refetch,
        "unsupported_for_prompt": unsupported_for_prompt,
        "prompt_ready": prompt_ready,
    }


def build_normalized_records(
    chinese_data_path: Path,
    card_data_cache_path: Path,
    cards_root: Path,
) -> dict[str, dict[str, Any]]:
    """Build normalized records from local inputs only."""
    chinese_records = load_card_chinese_data(chinese_data_path)
    chinese_by_key = {
        make_card_key(record.get("set_name"), record.get("number")): record
        for record in chinese_records
    }
    cache_by_raw_key = load_card_data_cache(card_data_cache_path)
    cache_by_key = {
        f"{record.get('set_name', '').upper()}-{normalize_number(record.get('number'))}": record
        for record in cache_by_raw_key.values()
    }
    all_keys = sorted(set(chinese_by_key) | set(cache_by_key))
    local_index = build_local_card_index(cards_root)

    records: dict[str, dict[str, Any]] = {}
    for normalized_lookup_key in all_keys:
        chinese_record = chinese_by_key.get(normalized_lookup_key)
        cache_record = cache_by_key.get(normalized_lookup_key)
        primary = chinese_record or cache_record or {}
        card_key = make_card_key(primary.get("set_name"), primary.get("number"))

        local_match, ambiguous_mapping = _resolve_local_match(chinese_record, cache_record, local_index)
        sources, field_source_map = _build_sources(chinese_record, cache_record, local_match)
        identity = _build_identity(card_key, chinese_record, cache_record, local_match, field_source_map)
        classification, untrusted_card_type, needs_type_refetch = _build_classification(
            local_match, cache_record, field_source_map
        )
        attacks, attacks_have_effect = _build_attacks(cache_record)
        abilities, abilities_have_effect = _build_abilities(cache_record)
        text, text_flags = _build_text(classification, attacks_have_effect or abilities_have_effect)

        quality_flags = {
            "missing_rules_text": text_flags["missing_rules_text"],
            "untrusted_card_type": untrusted_card_type,
            "missing_local_file": local_match is None,
            "ambiguous_mapping": ambiguous_mapping,
            "needs_text_refetch": text_flags["needs_text_refetch"],
            "needs_type_refetch": needs_type_refetch,
            "unsupported_for_prompt": text_flags["unsupported_for_prompt"] or ambiguous_mapping or local_match is None,
            "prompt_ready": (
                text_flags["prompt_ready"]
                and not ambiguous_mapping
                and local_match is not None
                and not untrusted_card_type
            ),
            "missing_effect_text": text_flags["missing_effect_text"],
        }

        if text["text_quality"] == "missing":
            field_source_map["text.text_quality"] = "missing"
        if quality_flags["missing_rules_text"]:
            field_source_map["quality_flags.missing_rules_text"] = "derived"
        if quality_flags["untrusted_card_type"]:
            field_source_map["quality_flags.untrusted_card_type"] = "derived"
        if quality_flags["missing_local_file"]:
            field_source_map["quality_flags.missing_local_file"] = "derived"

        records[card_key] = {
            "card_key": card_key,
            "identity": identity,
            "classification": classification,
            "text": text,
            "attacks": attacks,
            "abilities": abilities,
            "quality_flags": quality_flags,
            "provenance": {
                "sources": sources,
                "field_source_map": field_source_map,
            },
            "meta": {
                "schema_version": SCHEMA_VERSION,
                "generator_version": GENERATOR_VERSION,
            },
        }

    return records


__all__ = [
    "GENERATOR_VERSION",
    "SCHEMA_VERSION",
    "build_local_card_index",
    "build_normalized_records",
    "infer_local_card_class_info",
    "load_card_chinese_data",
    "load_card_data_cache",
    "make_card_key",
    "normalize_number",
]
