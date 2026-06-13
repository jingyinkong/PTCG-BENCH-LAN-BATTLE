"""In-memory dry-run patch application for normalized records.

Applies a single refetch result's ``normalized_patch_preview`` to an
existing normalized record without any network I/O, file reads, or file
writes.  The original record is never mutated — a deep copy is returned.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any


_TRAINER_BASES = {"Supporter", "Item", "Stadium", "Tool"}


def _is_trainer_like(classification: dict[str, Any]) -> bool:
    return classification.get("card_supertype") == "Trainer" or (
        classification.get("trainer_subtype") in _TRAINER_BASES
    )


def _is_supporter_like(classification: dict[str, Any]) -> bool:
    return (
        classification.get("card_supertype") == "Trainer"
        and classification.get("trainer_subtype") == "Supporter"
    )


@dataclass
class NormalizedPatchApplicationResult:
    card_key: str
    dry_run: bool = True
    applied: bool = False
    updated_record_preview: dict[str, Any] = field(default_factory=dict)
    application_report: dict[str, Any] = field(default_factory=dict)

    def asdict(self) -> dict[str, Any]:
        return {
            "card_key": self.card_key,
            "dry_run": self.dry_run,
            "applied": self.applied,
            "updated_record_preview": self.updated_record_preview,
            "application_report": self.application_report,
        }


def apply_refetch_result_to_normalized_record(
    record: dict[str, Any],
    refetch_result: dict[str, Any],
    *,
    allow_overwrite: bool = False,
) -> NormalizedPatchApplicationResult:
    """Apply *refetch_result* patch preview to *record* (in-memory, dry-run).

    Returns a :class:`NormalizedPatchApplicationResult` containing the
    updated record preview and a structured application report.  The
    original *record* is deep-copied and never modified.

    Safety rules — patch is **rejected** (``applied=False``) when:

    * ``refetch_result.errors`` is non-empty
    * ``response_diagnostics`` is missing
    * ``response_shape`` is ``"fetch_error"``
    * ``normalized_patch_preview`` is missing or empty
    * ``card_key`` mismatch between record and refetch result
    """
    card_key = record.get("card_key", "")

    # --- shared report fields ----------------------------------------------
    applied_fields: list[str] = []
    skipped_fields: list[dict[str, str]] = []
    warnings: list[str] = []
    errors: list[str] = []
    quality_flag_updates: dict[str, Any] = {}
    provenance_updates: dict[str, Any] = {}

    def _make_report() -> dict[str, Any]:
        return {
            "applied_fields": applied_fields,
            "skipped_fields": skipped_fields,
            "warnings": warnings,
            "errors": errors,
            "quality_flag_updates": quality_flag_updates,
            "provenance_updates": provenance_updates,
        }

    # --- deep copy the record ----------------------------------------------
    updated = copy.deepcopy(record)

    # --- safety rejections -------------------------------------------------
    refetch_errors: list[str] = list(refetch_result.get("errors") or [])
    if refetch_errors:
        errors.append("refetch_result_has_errors")
        return NormalizedPatchApplicationResult(
            card_key=card_key,
            applied=False,
            updated_record_preview=updated,
            application_report=_make_report(),
        )

    diagnostics: dict[str, Any] | None = refetch_result.get("response_diagnostics")
    if not diagnostics:
        errors.append("missing_response_diagnostics")
        return NormalizedPatchApplicationResult(
            card_key=card_key,
            applied=False,
            updated_record_preview=updated,
            application_report=_make_report(),
        )

    if diagnostics.get("response_shape") == "fetch_error":
        errors.append("fetch_error_response")
        return NormalizedPatchApplicationResult(
            card_key=card_key,
            applied=False,
            updated_record_preview=updated,
            application_report=_make_report(),
        )

    patch_preview: dict[str, Any] = refetch_result.get("normalized_patch_preview") or {}
    if not patch_preview:
        errors.append("empty_patch_preview")
        return NormalizedPatchApplicationResult(
            card_key=card_key,
            applied=False,
            updated_record_preview=updated,
            application_report=_make_report(),
        )

    result_card_key = refetch_result.get("card_key", "")
    if result_card_key != card_key:
        errors.append("card_key_mismatch")
        return NormalizedPatchApplicationResult(
            card_key=card_key,
            applied=False,
            updated_record_preview=updated,
            application_report=_make_report(),
        )

    # --- apply text fields -------------------------------------------------
    _apply_text_fields(
        updated=updated,
        patch_preview=patch_preview,
        diagnostics=diagnostics,
        allow_overwrite=allow_overwrite,
        applied_fields=applied_fields,
        skipped_fields=skipped_fields,
        warnings=warnings,
    )

    # --- apply classification fields ---------------------------------------
    _apply_classification_fields(
        updated=updated,
        patch_preview=patch_preview,
        diagnostics=diagnostics,
        allow_overwrite=allow_overwrite,
        applied_fields=applied_fields,
        skipped_fields=skipped_fields,
        warnings=warnings,
    )

    # --- update quality flags ----------------------------------------------
    _update_quality_flags(updated, applied_fields, quality_flag_updates)

    # --- update provenance -------------------------------------------------
    _update_provenance(updated, refetch_result, applied_fields, provenance_updates)

    # --- success -----------------------------------------------------------
    applied = len(applied_fields) > 0 or len(skipped_fields) == 0
    # Even if nothing was applied (e.g. all fields skipped), we still mark
    # applied=True when the safety checks passed and at least text or
    # classification were considered.
    if not applied and (diagnostics.get("has_description") or diagnostics.get("has_card_type")):
        applied = True

    return NormalizedPatchApplicationResult(
        card_key=card_key,
        applied=applied,
        updated_record_preview=updated,
        application_report=_make_report(),
    )


# ---------------------------------------------------------------------------
# text field application
# ---------------------------------------------------------------------------

_TEXT_FIELDS = ["rules_text_zh", "trainer_text_zh", "full_text_zh"]


def _apply_text_fields(
    *,
    updated: dict[str, Any],
    patch_preview: dict[str, Any],
    diagnostics: dict[str, Any],
    allow_overwrite: bool,
    applied_fields: list[str],
    skipped_fields: list[dict[str, str]],
    warnings: list[str],
) -> None:
    has_description = diagnostics.get("has_description", False)
    if not has_description:
        for field in _TEXT_FIELDS:
            skipped_fields.append({
                "field": f"text.{field}",
                "reason": "has_description_false",
            })
        return

    patch_text: dict[str, Any] = patch_preview.get("text") or {}
    existing_text: dict[str, Any] = updated.get("text") or {}

    for field in _TEXT_FIELDS:
        patch_value = patch_text.get(field)
        if patch_value is None or (isinstance(patch_value, str) and patch_value.strip() == ""):
            skipped_fields.append({
                "field": f"text.{field}",
                "reason": "patch_value_empty",
            })
            continue

        existing_value = existing_text.get(field)
        if existing_value is not None and existing_value != "":
            if allow_overwrite:
                if existing_text not in (updated.get("text"),):
                    updated.setdefault("text", {})[field] = patch_value
                else:
                    updated["text"][field] = patch_value
                applied_fields.append(f"text.{field}")
            else:
                skipped_fields.append({
                    "field": f"text.{field}",
                    "reason": "existing_value_present",
                })
        else:
            updated.setdefault("text", {})[field] = patch_value
            applied_fields.append(f"text.{field}")

    # If any text field was applied, mark text_available
    if any(f"text.{f}" in applied_fields for f in _TEXT_FIELDS):
        updated.setdefault("text", {})["text_available"] = True
        updated["text"]["text_quality"] = "refetched"


# ---------------------------------------------------------------------------
# classification field application
# ---------------------------------------------------------------------------

_CLASSIFICATION_FIELDS = ["card_supertype", "trainer_subtype"]


def _apply_classification_fields(
    *,
    updated: dict[str, Any],
    patch_preview: dict[str, Any],
    diagnostics: dict[str, Any],
    allow_overwrite: bool,
    applied_fields: list[str],
    skipped_fields: list[dict[str, str]],
    warnings: list[str],
) -> None:
    has_card_type = diagnostics.get("has_card_type", False)
    if not has_card_type:
        for field in _CLASSIFICATION_FIELDS:
            skipped_fields.append({
                "field": f"classification.{field}",
                "reason": "has_card_type_false",
            })
        return

    patch_class: dict[str, Any] = patch_preview.get("classification") or {}
    existing_class: dict[str, Any] = updated.get("classification") or {}
    existing_source: str = existing_class.get("classification_source", "")

    patch_supertype = patch_class.get("card_supertype")
    patch_subtype = patch_class.get("trainer_subtype")

    # --- card_supertype ----------------------------------------------------
    if patch_supertype is not None and patch_supertype != "":
        existing_supertype = existing_class.get("card_supertype")

        # Conflict check: local_class says one thing, patch says another
        if existing_source == "local_class" and existing_supertype and existing_supertype != patch_supertype:
            warnings.append("classification_conflict")
            skipped_fields.append({
                "field": "classification.card_supertype",
                "reason": "classification_conflict",
            })
            quality_flags = updated.setdefault("quality_flags", {})
            quality_flags["classification_conflict"] = True
        elif existing_supertype and existing_supertype == patch_supertype:
            # Same value — confirm / record
            applied_fields.append("classification.card_supertype")
        elif existing_supertype and existing_supertype != patch_supertype and not allow_overwrite:
            skipped_fields.append({
                "field": "classification.card_supertype",
                "reason": "existing_value_present",
            })
        else:
            updated.setdefault("classification", {})["card_supertype"] = patch_supertype
            applied_fields.append("classification.card_supertype")

    # --- trainer_subtype ---------------------------------------------------
    if patch_subtype is not None and patch_subtype != "" and patch_subtype != "Unknown":
        existing_subtype = existing_class.get("trainer_subtype")

        if existing_source == "local_class" and existing_subtype and existing_subtype != patch_subtype:
            warnings.append("classification_conflict")
            skipped_fields.append({
                "field": "classification.trainer_subtype",
                "reason": "classification_conflict",
            })
            quality_flags = updated.setdefault("quality_flags", {})
            quality_flags["classification_conflict"] = True
        elif existing_subtype and existing_subtype == patch_subtype:
            applied_fields.append("classification.trainer_subtype")
        elif existing_subtype and existing_subtype != patch_subtype and not allow_overwrite:
            skipped_fields.append({
                "field": "classification.trainer_subtype",
                "reason": "existing_value_present",
            })
        else:
            updated.setdefault("classification", {})["trainer_subtype"] = patch_subtype
            applied_fields.append("classification.trainer_subtype")


# ---------------------------------------------------------------------------
# quality flag updates
# ---------------------------------------------------------------------------


def _update_quality_flags(
    updated: dict[str, Any],
    applied_fields: list[str],
    quality_flag_updates: dict[str, Any],
) -> None:
    quality_flags = updated.setdefault("quality_flags", {})

    updated_any = False

    # If any text field was successfully applied
    if any(f"text.{f}" in applied_fields for f in _TEXT_FIELDS):
        if quality_flags.get("missing_rules_text"):
            quality_flags["missing_rules_text"] = False
            quality_flag_updates["missing_rules_text"] = "true→false"
            updated_any = True
        if quality_flags.get("needs_text_refetch"):
            quality_flags["needs_text_refetch"] = False
            quality_flag_updates["needs_text_refetch"] = "true→false"
            updated_any = True

    # If classification was trusted via refetch application
    if any(f"classification.{f}" in applied_fields for f in _CLASSIFICATION_FIELDS):
        if quality_flags.get("untrusted_card_type"):
            quality_flags["untrusted_card_type"] = False
            quality_flag_updates["untrusted_card_type"] = "true→false"
            updated_any = True

    # --- recalculate prompt_ready conservatively ---------------------------
    prompt_ready = _recompute_prompt_ready(updated)
    if quality_flags.get("prompt_ready") != prompt_ready:
        quality_flags["prompt_ready"] = prompt_ready
        quality_flag_updates["prompt_ready"] = f"{not prompt_ready}→{prompt_ready}"
        updated_any = True

    if not updated_any and not quality_flag_updates:
        quality_flag_updates["note"] = "no_quality_flag_changes"


def _recompute_prompt_ready(record: dict[str, Any]) -> bool:
    """Conservative prompt_ready recomputation.

    prompt_ready is true when:
    * The card is Trainer/Supporter
    * text.rules_text_zh or text.trainer_text_zh or text.full_text_zh is non-empty
    * local_file exists
    * no ambiguous_mapping
    * no classification_conflict
    """
    classification = record.get("classification") or {}
    identity = record.get("identity") or {}
    quality_flags = record.get("quality_flags") or {}
    text = record.get("text") or {}

    if quality_flags.get("classification_conflict"):
        return False
    if quality_flags.get("ambiguous_mapping"):
        return False
    if not identity.get("local_file"):
        return False

    is_trainer_supporter = _is_supporter_like(classification)
    if not is_trainer_supporter:
        return False

    has_text = bool(
        text.get("rules_text_zh")
        or text.get("trainer_text_zh")
        or text.get("full_text_zh")
    )
    if not has_text:
        return False

    return True


# ---------------------------------------------------------------------------
# provenance updates
# ---------------------------------------------------------------------------


def _update_provenance(
    updated: dict[str, Any],
    refetch_result: dict[str, Any],
    applied_fields: list[str],
    provenance_updates: dict[str, Any],
) -> None:
    provenance = updated.setdefault("provenance", {})
    field_source_map: dict[str, str] = provenance.setdefault("field_source_map", {})

    description_path = None
    card_type_path = None
    diagnostics = refetch_result.get("response_diagnostics")
    if isinstance(diagnostics, dict):
        description_path = diagnostics.get("description_path")
        card_type_path = diagnostics.get("card_type_path")

    source_name = "tcg.mik.card-detail"

    for field_path in applied_fields:
        if field_path.startswith("text."):
            field_source_map[field_path] = f"{source_name}.description"
        elif field_path.startswith("classification."):
            field_source_map[field_path] = f"{source_name}.cardType"

    # Merge provenance_preview from refetch result (safe fields only)
    provenance_preview = refetch_result.get("provenance_preview")
    if isinstance(provenance_preview, dict):
        provenance["refetch"] = {
            "source": provenance_preview.get("source_api", source_name),
            "source_ids": provenance_preview.get("source_ids", {}),
            "response_shape": diagnostics.get("response_shape") if diagnostics else "unknown",
        }
        if description_path:
            provenance["refetch"]["description_path"] = description_path
        if card_type_path:
            provenance["refetch"]["card_type_path"] = card_type_path

    # Append a source entry if not already present
    sources: list[dict[str, Any]] = provenance.get("sources") or []
    refetch_source_entry = {
        "id": source_name,
        "type": "refetch",
        "applied_fields": list(applied_fields),
    }
    sources.append(refetch_source_entry)
    provenance["sources"] = sources

    provenance_updates["field_source_map_keys"] = sorted(
        k for k in field_source_map if k in applied_fields
    )
    provenance_updates["sources_added"] = source_name


__all__ = [
    "NormalizedPatchApplicationResult",
    "apply_refetch_result_to_normalized_record",
]
