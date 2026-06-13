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


def parse_tcg_mik_card_detail_response(
    response: dict[str, Any],
    dry_run_request: dict[str, Any],
) -> dict[str, Any]:
    """Parse a (mock or real) card-detail response into a unified preview."""
    errors: list[str] = []
    warnings: list[str] = []

    raw_fields_found: list[str] = []
    parsed_fields: dict[str, Any] = {}

    # --- cardType -------------------------------------------------------
    raw_card_type = response.get("cardType")
    if raw_card_type is not None:
        raw_fields_found.append("cardType")
        parsed_fields["cardType"] = raw_card_type

    # --- description ----------------------------------------------------
    raw_description = response.get("description")
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
    if "cardType" in field_mapping and raw_card_type is not None:
        supertype, subtype = _map_card_type(raw_card_type, warnings)
        target_keys = field_mapping["cardType"]
        for idx, key in enumerate(target_keys):
            val = supertype if idx == 0 else subtype
            if val is not None:
                _apply_patch(patch, [key], val)

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
