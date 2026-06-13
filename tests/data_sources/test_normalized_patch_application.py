"""Tests for normalized_patch_application.py — in-memory dry-run only."""

from __future__ import annotations

import ast
import copy
from pathlib import Path

from ptcg.data_sources.normalized_patch_application import (
    apply_refetch_result_to_normalized_record,
)

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "ptcg" / "data_sources" / "normalized_patch_application.py"

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _twm145_record() -> dict:
    """Existing normalized TWM-145 record before patch application."""
    return {
        "card_key": "TWM-145",
        "identity": {
            "card_key": "TWM-145",
            "set_code": "TWM",
            "set_name": "Twilight Masquerade",
            "number": "145",
            "normalized_number": "145",
            "name_en": "Carmine",
            "name_zh": "丹瑜",
            "local_file": "ptcg/cards/TWM/twm145carmine.py",
            "local_class_name": "TWM145Carmine",
            "source_ids": {
                "card_chinese_key": "...",
                "card_data_cache_key": "TWM-145",
            },
        },
        "classification": {
            "card_supertype": "Trainer",
            "trainer_subtype": "Supporter",
            "pokemon_stage": None,
            "energy_type": None,
            "classification_confidence": "high",
            "classification_source": "local_class",
            "classification_warnings": ["card_type_conflict", "card_data_cache.card_type_untrusted"],
        },
        "text": {
            "rules_text_zh": None,
            "rules_text_en": None,
            "trainer_text_zh": None,
            "trainer_text_en": None,
            "full_text_zh": None,
            "full_text_en": None,
            "text_available": False,
            "text_quality": "missing",
        },
        "attacks": [],
        "abilities": [],
        "quality_flags": {
            "missing_rules_text": True,
            "untrusted_card_type": True,
            "missing_local_file": False,
            "ambiguous_mapping": False,
            "needs_text_refetch": True,
            "needs_type_refetch": False,
            "unsupported_for_prompt": True,
            "prompt_ready": False,
            "missing_effect_text": False,
        },
        "provenance": {
            "sources": [
                {"id": "card_chinese_data", "type": "json", "path": "card_chinese_data.json"},
                {"id": "card_data_cache", "type": "json", "path": "card_data_cache.json"},
                {"id": "local_class", "type": "python", "path": "ptcg/cards/TWM/twm145carmine.py"},
            ],
            "field_source_map": {
                "classification.card_supertype": "local_class",
                "classification.trainer_subtype": "local_class",
                "identity.local_file": "local_class",
                "identity.local_class_name": "local_class",
            },
        },
        "meta": {
            "schema_version": "1.0",
            "generator_version": "0.1.0",
        },
    }


def _twm145_refetch_result(**overrides: object) -> dict:
    """Successful TWM-145 refetch result fixture."""
    result: dict = {
        "card_key": "TWM-145",
        "source": "tcg.mik.moe card-detail",
        "raw_fields_found": ["cardType", "description"],
        "parsed_fields": {
            "cardType": "Supporter",
            "description": (
                "将自己的手牌全部放回牌库并重洗。然后，从牌库上方抽出5张卡。"
            ),
        },
        "normalized_patch_preview": {
            "text": {
                "rules_text_zh": "将自己的手牌全部放回牌库并重洗。然后，从牌库上方抽出5张卡。",
                "trainer_text_zh": "将自己的手牌全部放回牌库并重洗。然后，从牌库上方抽出5张卡。",
                "full_text_zh": "将自己的手牌全部放回牌库并重洗。然后，从牌库上方抽出5张卡。",
            },
            "classification": {
                "card_supertype": "Trainer",
                "trainer_subtype": "Supporter",
            },
        },
        "provenance_preview": {
            "source_api": "tcg.mik.moe card-detail",
            "dry_run": True,
        },
        "dry_run": True,
        "will_write_files": False,
        "network_enabled": True,
        "response_diagnostics": {
            "top_level_keys": ["cardType", "description"],
            "candidate_paths_checked": ["$.description", "$.cardType"],
            "description_path": "$.description",
            "card_type_path": "$.cardType",
            "has_description": True,
            "has_card_type": True,
            "response_shape": "flat",
            "safe_preview": {"top_level_keys": ["cardType", "description"]},
        },
        "errors": [],
        "warnings": [],
    }
    result.update(overrides)  # type: ignore[arg-type]
    return result


# ---------------------------------------------------------------------------
# 1. Successful TWM-145 patch application
# ---------------------------------------------------------------------------


def test_successful_twm145_patch_application():
    record = _twm145_record()
    original = copy.deepcopy(record)
    refetch = _twm145_refetch_result()

    result = apply_refetch_result_to_normalized_record(record, refetch)

    # --- result structure ---
    assert result.card_key == "TWM-145"
    assert result.dry_run is True
    assert result.applied is True

    # --- text fields applied ---
    preview = result.updated_record_preview
    assert preview["text"]["rules_text_zh"] is not None
    assert preview["text"]["trainer_text_zh"] is not None
    assert preview["text"]["full_text_zh"] is not None
    assert "将自己的手牌全部放回牌库并重洗" in preview["text"]["rules_text_zh"]
    assert preview["text"]["text_available"] is True
    assert preview["text"]["text_quality"] == "refetched"

    # --- classification kept ---
    assert preview["classification"]["card_supertype"] == "Trainer"
    assert preview["classification"]["trainer_subtype"] == "Supporter"

    # --- quality flags updated ---
    flags = preview["quality_flags"]
    assert flags["missing_rules_text"] is False
    assert flags["needs_text_refetch"] is False
    assert flags["untrusted_card_type"] is False

    # --- prompt_ready recomputed ---
    assert flags["prompt_ready"] is True
    assert "prompt_ready" in result.application_report["quality_flag_updates"]

    # --- provenance updated ---
    field_source_map = preview["provenance"]["field_source_map"]
    assert "text.rules_text_zh" in field_source_map
    assert "text.trainer_text_zh" in field_source_map
    assert "text.full_text_zh" in field_source_map
    assert "classification.trainer_subtype" in field_source_map
    assert field_source_map["text.rules_text_zh"] == "tcg.mik.card-detail.description"

    # --- refetch in provenance ---
    assert "refetch" in preview["provenance"]

    # --- original record not mutated ---
    assert original["text"]["rules_text_zh"] is None
    assert original["quality_flags"]["missing_rules_text"] is True

    # --- report ---
    report = result.application_report
    assert len(report["applied_fields"]) > 0
    assert "text.rules_text_zh" in report["applied_fields"]
    assert len(report["errors"]) == 0


# ---------------------------------------------------------------------------
# 2. Errors non-empty does not apply
# ---------------------------------------------------------------------------


def test_errors_non_empty_does_not_apply():
    record = _twm145_record()
    refetch = _twm145_refetch_result(errors=["request_failed"])

    result = apply_refetch_result_to_normalized_record(record, refetch)

    assert result.applied is False
    assert "refetch_result_has_errors" in result.application_report["errors"]
    # updated_record_preview should equal original record (deep copy)
    assert result.updated_record_preview["text"]["rules_text_zh"] is None


# ---------------------------------------------------------------------------
# 3. Missing description does not write text
# ---------------------------------------------------------------------------


def test_missing_description_skips_text():
    record = _twm145_record()
    refetch = _twm145_refetch_result()
    refetch["response_diagnostics"]["has_description"] = False
    # still has text in patch preview (should be skipped)
    refetch["normalized_patch_preview"]["text"]["rules_text_zh"] = "Some text"

    result = apply_refetch_result_to_normalized_record(record, refetch)

    preview = result.updated_record_preview
    # text should not be applied
    assert preview["text"]["rules_text_zh"] is None

    skipped = result.application_report["skipped_fields"]
    text_skipped = [s for s in skipped if s["field"].startswith("text.")]
    assert len(text_skipped) == 3  # rules, trainer, full
    assert all(s["reason"] == "has_description_false" for s in text_skipped)


# ---------------------------------------------------------------------------
# 4. Missing cardType does not write classification
# ---------------------------------------------------------------------------


def test_missing_card_type_skips_classification():
    record = _twm145_record()
    refetch = _twm145_refetch_result()
    refetch["response_diagnostics"]["has_card_type"] = False
    refetch["normalized_patch_preview"]["classification"] = {
        "card_supertype": "Pokemon",  # wrong, should not be applied
        "trainer_subtype": "Unknown",
    }

    result = apply_refetch_result_to_normalized_record(record, refetch)

    preview = result.updated_record_preview
    # classification should remain Trainer/Supporter (from local)
    assert preview["classification"]["card_supertype"] == "Trainer"
    assert preview["classification"]["trainer_subtype"] == "Supporter"

    skipped = result.application_report["skipped_fields"]
    cls_skipped = [s for s in skipped if s["field"].startswith("classification.")]
    assert len(cls_skipped) == 2
    assert all(s["reason"] == "has_card_type_false" for s in cls_skipped)


# ---------------------------------------------------------------------------
# 5. Existing non-empty field default no overwrite
# ---------------------------------------------------------------------------


def test_existing_non_empty_field_no_overwrite():
    record = _twm145_record()
    # Simulate an existing text value
    record["text"]["rules_text_zh"] = "Existing text"
    original_text = record["text"]["rules_text_zh"]

    refetch = _twm145_refetch_result()

    result = apply_refetch_result_to_normalized_record(record, refetch)

    preview = result.updated_record_preview
    # rules_text_zh should keep old value
    assert preview["text"]["rules_text_zh"] == original_text

    skipped = result.application_report["skipped_fields"]
    rules_skipped = [s for s in skipped if s["field"] == "text.rules_text_zh"]
    assert len(rules_skipped) == 1
    assert rules_skipped[0]["reason"] == "existing_value_present"


# ---------------------------------------------------------------------------
# 6. allow_overwrite=True overrides non-empty field
# ---------------------------------------------------------------------------


def test_allow_overwrite_overrides_non_empty_field():
    record = _twm145_record()
    record["text"]["rules_text_zh"] = "Old text"
    refetch = _twm145_refetch_result()

    result = apply_refetch_result_to_normalized_record(
        record, refetch, allow_overwrite=True
    )

    preview = result.updated_record_preview
    assert "将自己的手牌全部放回牌库并重洗" in preview["text"]["rules_text_zh"]
    assert "text.rules_text_zh" in result.application_report["applied_fields"]


# ---------------------------------------------------------------------------
# 7. card_key mismatch does not apply
# ---------------------------------------------------------------------------


def test_card_key_mismatch():
    record = _twm145_record()
    refetch = _twm145_refetch_result(card_key="SSH-178")

    result = apply_refetch_result_to_normalized_record(record, refetch)

    assert result.applied is False
    assert "card_key_mismatch" in result.application_report["errors"]


# ---------------------------------------------------------------------------
# 8. fetch_error response_shape does not apply
# ---------------------------------------------------------------------------


def test_fetch_error_response_shape():
    record = _twm145_record()
    refetch = _twm145_refetch_result()
    refetch["response_diagnostics"]["response_shape"] = "fetch_error"

    result = apply_refetch_result_to_normalized_record(record, refetch)

    assert result.applied is False
    assert "fetch_error_response" in result.application_report["errors"]


# ---------------------------------------------------------------------------
# 9. Classification conflict does not overwrite (local_class Pokemon vs refetch Supporter)
# ---------------------------------------------------------------------------


def test_classification_conflict_no_overwrite():
    record = _twm145_record()
    # Change local classification to Pokemon
    record["classification"] = {
        "card_supertype": "Pokemon",
        "trainer_subtype": "Unknown",
        "pokemon_stage": "Basic",
        "energy_type": None,
        "classification_confidence": "high",
        "classification_source": "local_class",
        "classification_warnings": [],
    }
    # Refetch says Trainer/Supporter
    refetch = _twm145_refetch_result()

    result = apply_refetch_result_to_normalized_record(record, refetch)

    preview = result.updated_record_preview
    # classification should NOT be overwritten
    assert preview["classification"]["card_supertype"] == "Pokemon"
    assert preview["classification"]["trainer_subtype"] == "Unknown"

    # warnings should report conflict
    assert "classification_conflict" in result.application_report["warnings"]

    skipped = result.application_report["skipped_fields"]
    card_supertype_skipped = [
        s for s in skipped if s["field"] == "classification.card_supertype"
    ]
    assert len(card_supertype_skipped) >= 1
    assert any(s["reason"] == "classification_conflict" for s in skipped)

    # quality_flags should reflect conflict
    assert preview["quality_flags"].get("classification_conflict") is True


# ---------------------------------------------------------------------------
# 10. No IO / no network
# ---------------------------------------------------------------------------


def test_no_network_imports():
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden = {"requests", "httpx", "aiohttp", "bs4", "urllib.request", "urllib"}
    imported: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])

    assert forbidden.isdisjoint(imported), f"Found forbidden import: {imported & forbidden}"


def test_no_file_operations():
    source = MODULE_PATH.read_text(encoding="utf-8")
    write_patterns = ["write_text", ".write(", "json.dump"]
    for pattern in write_patterns:
        assert pattern not in source, f"Found forbidden write pattern: {pattern}"


# ---------------------------------------------------------------------------
# 11. Missing response_diagnostics
# ---------------------------------------------------------------------------


def test_missing_response_diagnostics():
    record = _twm145_record()
    refetch = _twm145_refetch_result()
    del refetch["response_diagnostics"]

    result = apply_refetch_result_to_normalized_record(record, refetch)

    assert result.applied is False
    assert "missing_response_diagnostics" in result.application_report["errors"]


# ---------------------------------------------------------------------------
# 12. Empty patch_preview
# ---------------------------------------------------------------------------


def test_empty_patch_preview():
    record = _twm145_record()
    refetch = _twm145_refetch_result()
    refetch["normalized_patch_preview"] = {}

    result = apply_refetch_result_to_normalized_record(record, refetch)

    assert result.applied is False
    assert "empty_patch_preview" in result.application_report["errors"]


# ---------------------------------------------------------------------------
# 13. Provenance field_source_map records correct source
# ---------------------------------------------------------------------------


def test_provenance_field_source_map_correct():
    record = _twm145_record()
    refetch = _twm145_refetch_result()

    result = apply_refetch_result_to_normalized_record(record, refetch)
    preview = result.updated_record_preview

    fsm = preview["provenance"]["field_source_map"]
    # text fields should come from description
    for field_name in ("text.rules_text_zh", "text.trainer_text_zh", "text.full_text_zh"):
        assert field_name in fsm, f"Missing {field_name} in field_source_map"
        assert fsm[field_name] == "tcg.mik.card-detail.description"

    # classification should come from cardType
    if "classification.card_supertype" in fsm:
        assert fsm["classification.card_supertype"] == "tcg.mik.card-detail.cardType"
    if "classification.trainer_subtype" in fsm:
        assert fsm["classification.trainer_subtype"] == "tcg.mik.card-detail.cardType"

    # provenance should have refetch entry
    assert "refetch" in preview["provenance"]
    assert preview["provenance"]["refetch"]["source"] == "tcg.mik.moe card-detail"

    # report provenance_updates
    updates = result.application_report["provenance_updates"]
    assert "sources_added" in updates


# ---------------------------------------------------------------------------
# 14. Original record not mutated
# ---------------------------------------------------------------------------


def test_original_record_not_mutated():
    record = _twm145_record()
    original_text_available = record["text"]["text_available"]
    original_quality_missing_rules = record["quality_flags"]["missing_rules_text"]
    original_prompt_ready = record["quality_flags"]["prompt_ready"]

    refetch = _twm145_refetch_result()
    apply_refetch_result_to_normalized_record(record, refetch)

    # original record MUST be unchanged
    assert record["text"]["text_available"] == original_text_available
    assert record["quality_flags"]["missing_rules_text"] == original_quality_missing_rules
    assert record["quality_flags"]["prompt_ready"] == original_prompt_ready
    assert record["text"]["rules_text_zh"] is None


# ---------------------------------------------------------------------------
# 15. Result structure consistency
# ---------------------------------------------------------------------------


def test_result_dataclass_structure():
    record = _twm145_record()
    refetch = _twm145_refetch_result()
    result = apply_refetch_result_to_normalized_record(record, refetch)

    d = result.asdict()
    assert set(d) == {"card_key", "dry_run", "applied", "updated_record_preview", "application_report"}
    assert d["dry_run"] is True
    assert isinstance(d["application_report"], dict)
    report = d["application_report"]
    assert set(report) == {
        "applied_fields", "skipped_fields", "warnings", "errors",
        "quality_flag_updates", "provenance_updates",
    }


# ---------------------------------------------------------------------------
# 16. prompt_ready stays false when conditions not met
# ---------------------------------------------------------------------------


def test_prompt_ready_stays_false_when_no_local_file():
    record = _twm145_record()
    record["identity"]["local_file"] = None
    refetch = _twm145_refetch_result()

    result = apply_refetch_result_to_normalized_record(record, refetch)
    assert result.updated_record_preview["quality_flags"]["prompt_ready"] is False


def test_prompt_ready_stays_false_when_not_supporter():
    record = _twm145_record()
    record["classification"]["trainer_subtype"] = "Item"
    refetch = _twm145_refetch_result()

    result = apply_refetch_result_to_normalized_record(record, refetch)
    assert result.updated_record_preview["quality_flags"]["prompt_ready"] is False


def test_prompt_ready_stays_false_when_ambiguous():
    record = _twm145_record()
    record["quality_flags"]["ambiguous_mapping"] = True
    refetch = _twm145_refetch_result()

    result = apply_refetch_result_to_normalized_record(record, refetch)
    assert result.updated_record_preview["quality_flags"]["prompt_ready"] is False


# ---------------------------------------------------------------------------
# 17. patch_value_empty skips field
# ---------------------------------------------------------------------------


def test_patch_value_empty_skips_field():
    record = _twm145_record()
    refetch = _twm145_refetch_result()
    refetch["normalized_patch_preview"]["text"]["rules_text_zh"] = ""

    result = apply_refetch_result_to_normalized_record(record, refetch)
    skipped = result.application_report["skipped_fields"]
    rules_skipped = [s for s in skipped if s["field"] == "text.rules_text_zh"]
    assert len(rules_skipped) == 1
    assert rules_skipped[0]["reason"] == "patch_value_empty"
