"""Targeted text refetch client skeleton for tcg.mik.moe card-detail.

Provides a safe-by-default client that only performs network requests
when explicitly enabled and wired with a fetcher callable.  In dry-run
mode (the default) it returns a blocked/skipped result without any I/O.
"""

from __future__ import annotations

from typing import Any, Callable

_CARD_TYPE_MAP: dict[str, tuple[str, str | None]] = {
    "Supporter": ("Trainer", "Supporter"),
    "Item": ("Trainer", "Item"),
    "Stadium": ("Trainer", "Stadium"),
    "Tool": ("Trainer", "Tool"),
    "Pokemon": ("Pokemon", None),
    "Energy": ("Energy", None),
}

# Priority-ordered paths the parser checks for description and cardType.
# Each entry: (path_label, key_chain)
_PARSER_CANDIDATE_PATHS: list[tuple[str, list[str]]] = [
    ("$.description", ["description"]),
    ("$.cardType", ["cardType"]),
    ("$.data.description", ["data", "description"]),
    ("$.data.cardType", ["data", "cardType"]),
    ("$.data.card.description", ["data", "card", "description"]),
    ("$.data.card.cardType", ["data", "card", "cardType"]),
    ("$.card.description", ["card", "description"]),
    ("$.card.cardType", ["card", "cardType"]),
    ("$.result.description", ["result", "description"]),
    ("$.result.cardType", ["result", "cardType"]),
]

# Fields that MUST NOT appear in safe_preview (blacklist of large/raw fields).
_SAFE_PREVIEW_BLOCKED_KEYS: frozenset[str] = frozenset({
    "image", "html", "giant_text", "giantText",
    "cardImage", "card_image", "raw", "fullCard",
})

# Maximum depth for safe_preview key traversal.
_SAFE_PREVIEW_MAX_DEPTH = 3

# Signature expected for injected fetchers:
#   Callable[[dict], dict]
Fetcher = Callable[[dict[str, Any]], dict[str, Any]]


class TcgMikRefetchClient:
    """Safe-by-default client for tcg.mik.moe card-detail fetches.

    *network_enabled=False* is the default; without it (and without an
    explicit *fetcher*) every call to :meth:`fetch_detail_for_request`
    returns a blocked result.
    """

    def __init__(
        self,
        fetcher: Fetcher | None = None,
        network_enabled: bool = False,
    ) -> None:
        self._fetcher = fetcher
        self._network_enabled = network_enabled

    @property
    def network_enabled(self) -> bool:
        return self._network_enabled

    def fetch_detail_for_request(self, dry_run_request: dict[str, Any]) -> dict[str, Any]:
        """Return a parsed preview dict for *dry_run_request*.

        When *network_enabled* is ``False`` or no *fetcher* has been
        injected the call is **blocked** and the result carries
        ``network_disabled`` in ``errors``.
        """
        if not self._network_enabled or self._fetcher is None:
            return _blocked_result(dry_run_request)

        raw_response = self._fetcher(dry_run_request)
        return parse_tcg_mik_card_detail_response(raw_response, dry_run_request)


# ---------------------------------------------------------------------------
# response diagnostics
# ---------------------------------------------------------------------------


def _try_extract_field(
    response: dict[str, Any],
    field_name: str,
) -> tuple[Any, str | None]:
    """Extract *field_name* from *response* trying 5 wrapper shapes.

    Priority order:
      1. top-level  (``$.{field}``)
      2. data        (``$.data.{field}``)
      3. data.card   (``$.data.card.{field}``)
      4. card        (``$.card.{field}``)
      5. result      (``$.result.{field}``)

    Returns ``(value, path_label)`` where *path_label* is the first
    matching JSONPath-like string, or ``(None, None)`` if not found.
    """
    wrappers: list[tuple[str, list[Any]]] = [
        ("$.{f}", []),
        ("$.data.{f}", ["data"]),
        ("$.data.card.{f}", ["data", "card"]),
        ("$.card.{f}", ["card"]),
        ("$.result.{f}", ["result"]),
    ]
    for template, chain in wrappers:
        container = response
        for key in chain:
            if not isinstance(container, dict):
                break
            container = container.get(key)
        if isinstance(container, dict) and field_name in container:
            value = container[field_name]
            if value is not None:
                return value, template.format(f=field_name)
    return None, None


def _build_response_diagnostics(response: Any) -> dict[str, Any]:
    """Build a diagnostics block from a raw API response.

    Never includes full field values — only structural summaries.
    """
    candidate_paths_checked: list[str] = [p for p, _ in _PARSER_CANDIDATE_PATHS]

    # --- invalid shape --------------------------------------------------
    if not isinstance(response, dict):
        return {
            "top_level_keys": [],
            "candidate_paths_checked": candidate_paths_checked,
            "description_path": None,
            "card_type_path": None,
            "has_description": False,
            "has_card_type": False,
            "response_shape": "invalid",
            "safe_preview": {
                "type": type(response).__name__,
                "note": "response is not a dict — cannot parse",
            },
        }

    top_level_keys = list(response.keys())

    # --- safe_preview ---------------------------------------------------
    safe: dict[str, Any] = {"top_level_keys": top_level_keys}
    # shallow copy of code / message / status (API error shape)
    for _k in ("code", "message", "status"):
        if _k in response and not isinstance(response[_k], (dict, list)):
            safe[_k] = response[_k]

    # data keys (shallow)
    data = response.get("data")
    if isinstance(data, dict):
        safe["data_keys"] = _safe_shallow_keys(data)
        card = data.get("card")
        if isinstance(card, dict):
            safe["card_keys"] = _safe_shallow_keys(card)

    # card keys (shallow, direct wrapper)
    card = response.get("card")
    if isinstance(card, dict) and "card_keys" not in safe:
        safe["card_keys"] = _safe_shallow_keys(card)

    # --- extract description / cardType ---------------------------------
    raw_description, description_path = _try_extract_field(response, "description")
    raw_card_type, card_type_path = _try_extract_field(response, "cardType")

    # --- response_shape ------------------------------------------------
    response_shape = _determine_shape(description_path)

    return {
        "top_level_keys": top_level_keys,
        "candidate_paths_checked": candidate_paths_checked,
        "description_path": description_path,
        "card_type_path": card_type_path,
        "has_description": (
            description_path is not None
            and raw_description is not None
            and isinstance(raw_description, str)
            and raw_description.strip() != ""
        ),
        "has_card_type": card_type_path is not None,
        "response_shape": response_shape,
        "safe_preview": safe,
    }


def _safe_shallow_keys(d: dict[str, Any]) -> list[str]:
    """Return keys of *d*, excluding large/blacklisted keys."""
    return [k for k in d if k not in _SAFE_PREVIEW_BLOCKED_KEYS]


def _determine_shape(description_path: str | None) -> str:
    """Map the description JSONPath to a response_shape label."""
    if description_path is None:
        return "unknown"
    if description_path.startswith("$.data.card."):
        return "wrapped_data_card"
    if description_path.startswith("$.data."):
        return "wrapped_data"
    if description_path.startswith("$.card."):
        return "wrapped_card"
    if description_path.startswith("$.result."):
        return "wrapped_result"
    return "flat"


# ---------------------------------------------------------------------------
# parse
# ---------------------------------------------------------------------------


def parse_tcg_mik_card_detail_response(
    response: Any,
    dry_run_request: dict[str, Any],
) -> dict[str, Any]:
    """Parse a (mock or real) card-detail response into a unified preview.

    Supports 5 response wrapper shapes (flat, data, data.card, card,
    result) and includes *response_diagnostics* for debugging missing
    fields.
    """
    errors: list[str] = []
    warnings: list[str] = []

    raw_fields_found: list[str] = []
    parsed_fields: dict[str, Any] = {}

    # --- diagnostics (built before parsing so it's always present) ------
    diagnostics = _build_response_diagnostics(response)

    # --- invalid response shape -----------------------------------------
    if not isinstance(response, dict):
        return {
            "card_key": dry_run_request.get("card_key"),
            "source": dry_run_request.get("source"),
            "raw_fields_found": [],
            "parsed_fields": {},
            "normalized_patch_preview": {},
            "provenance_preview": {
                "source_api": dry_run_request.get("source"),
                "dry_run": True,
            },
            "dry_run": True,
            "will_write_files": False,
            "network_enabled": dry_run_request.get("network_enabled", False),
            "response_diagnostics": diagnostics,
            "errors": ["invalid_response_shape"],
            "warnings": [],
        }

    # --- cardType -------------------------------------------------------
    raw_card_type, _ct_path = _try_extract_field(response, "cardType")
    if raw_card_type is not None:
        raw_fields_found.append("cardType")
        parsed_fields["cardType"] = raw_card_type

    # --- description ----------------------------------------------------
    raw_description, _desc_path = _try_extract_field(response, "description")
    if raw_description is not None:
        raw_fields_found.append("description")
        parsed_fields["description"] = raw_description

    # --- pokemonAttr ----------------------------------------------------
    pokemon_attr = response.get("pokemonAttr", {})
    attacks_raw = pokemon_attr.get("attack") if isinstance(pokemon_attr, dict) else None
    abilities_raw = pokemon_attr.get("ability") if isinstance(pokemon_attr, dict) else None

    if attacks_raw:
        raw_fields_found.append("pokemonAttr.attack")
        parsed_fields["pokemonAttr.attack"] = attacks_raw
    if abilities_raw:
        raw_fields_found.append("pokemonAttr.ability")
        parsed_fields["pokemonAttr.ability"] = abilities_raw

    # --- normalized_patch_preview ---------------------------------------
    field_mapping: dict[str, list[str]] = dry_run_request.get("field_mapping", {})
    patch: dict[str, Any] = {}

    # description → text.*
    if "description" in field_mapping:
        if raw_description and isinstance(raw_description, str) and raw_description.strip():
            target_keys = field_mapping["description"]
            _apply_patch(patch, target_keys, raw_description)
        else:
            errors.append("missing_description")

    # cardType → classification.*
    if "cardType" in field_mapping:
        if raw_card_type is not None:
            supertype, subtype = _map_card_type(raw_card_type, warnings)
            target_keys = field_mapping["cardType"]
            for idx, key in enumerate(target_keys):
                val = supertype if idx == 0 else subtype
                if val is not None:
                    _apply_patch(patch, [key], val)
        else:
            warnings.append("missing_card_type")

    # pokemonAttr.attack[].text → attacks[].effect_text_zh
    if "pokemonAttr.attack[].text" in field_mapping and attacks_raw:
        attack_previews: list[dict[str, Any]] = []
        for atk in attacks_raw if isinstance(attacks_raw, list) else []:
            if isinstance(atk, dict) and atk.get("text"):
                attack_previews.append({
                    "name": atk.get("name", ""),
                    "effect_text_zh": atk.get("text", ""),
                })
        if attack_previews:
            patch["attacks"] = attack_previews

    # pokemonAttr.ability[].text → abilities[].effect_text_zh
    if "pokemonAttr.ability[].text" in field_mapping and abilities_raw:
        ability_previews: list[dict[str, Any]] = []
        for abi in abilities_raw if isinstance(abilities_raw, list) else []:
            if isinstance(abi, dict) and abi.get("text"):
                ability_previews.append({
                    "name": abi.get("name", ""),
                    "effect_text_zh": abi.get("text", ""),
                })
        if ability_previews:
            patch["abilities"] = ability_previews

    return {
        "card_key": dry_run_request.get("card_key"),
        "source": dry_run_request.get("source"),
        "raw_fields_found": raw_fields_found,
        "parsed_fields": parsed_fields,
        "normalized_patch_preview": patch,
        "provenance_preview": {
            "source_api": dry_run_request.get("source"),
            "dry_run": True,
        },
        "dry_run": True,
        "will_write_files": False,
        "network_enabled": dry_run_request.get("network_enabled", False),
        "response_diagnostics": diagnostics,
        "errors": errors,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _blocked_result(dry_run_request: dict[str, Any]) -> dict[str, Any]:
    return {
        "card_key": dry_run_request.get("card_key"),
        "source": dry_run_request.get("source"),
        "raw_fields_found": [],
        "parsed_fields": {},
        "normalized_patch_preview": {},
        "provenance_preview": {
            "source_api": dry_run_request.get("source"),
            "dry_run": True,
        },
        "dry_run": True,
        "will_write_files": False,
        "network_enabled": dry_run_request.get("network_enabled", False),
        "response_diagnostics": {
            "top_level_keys": [],
            "candidate_paths_checked": [p for p, _ in _PARSER_CANDIDATE_PATHS],
            "description_path": None,
            "card_type_path": None,
            "has_description": False,
            "has_card_type": False,
            "response_shape": "blocked",
            "safe_preview": {"note": "network disabled — no response"},
        },
        "errors": ["network_disabled"],
        "warnings": [],
    }


def _map_card_type(
    raw: str,
    warnings: list[str],
) -> tuple[str, str | None]:
    entry = _CARD_TYPE_MAP.get(raw)
    if entry is None:
        warnings.append("unknown_card_type")
        return ("Unknown", None)
    return entry


def _apply_patch(
    patch: dict[str, Any],
    keys: list[str],
    value: Any,
) -> None:
    for key in keys:
        parts = key.split(".")
        container = patch
        for part in parts[:-1]:
            container = container.setdefault(part, {})
        container[parts[-1]] = value


__all__ = [
    "TcgMikRefetchClient",
    "parse_tcg_mik_card_detail_response",
]
