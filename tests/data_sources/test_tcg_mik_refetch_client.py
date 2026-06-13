import ast
from pathlib import Path

from ptcg.data_sources.tcg_mik_refetch_client import (
    TcgMikRefetchClient,
    parse_tcg_mik_card_detail_response,
)

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "ptcg" / "data_sources" / "tcg_mik_refetch_client.py"

_NO_WRITE_PATTERNS = {
    "Path.write_text",
    "open(",
    "json.dump",
    ".write(",
}

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _supporter_dry_run_request(**overrides: object) -> dict:
    req: dict = {
        "card_key": "TWM-145",
        "name_en": "Carmine",
        "name_zh": "丹瑜",
        "can_refetch": True,
        "method": "GET",
        "source": "tcg.mik.moe card-detail",
        "lookup_strategy": "detail_by_source_ids",
        "lookup": {},
        "expected_source_fields": ["description", "cardType"],
        "field_mapping": {
            "description": [
                "text.rules_text_zh",
                "text.trainer_text_zh",
                "text.full_text_zh",
            ],
            "cardType": [
                "classification.card_supertype",
                "classification.trainer_subtype",
            ],
        },
        "desired_fields": [
            "rules_text_zh",
            "trainer_text_zh",
            "full_text_zh",
            "card_supertype",
            "trainer_subtype",
        ],
        "dry_run": True,
        "will_write_files": False,
        "network_enabled": False,
        "blocking_issues": [],
        "notes": [],
    }
    req.update(overrides)  # type: ignore[arg-type]
    return req


def _pokemon_dry_run_request(**overrides: object) -> dict:
    return {
        "card_key": "PKM-1",
        "name_en": "TestMon",
        "name_zh": "Test",
        "can_refetch": True,
        "method": "GET",
        "source": "tcg.mik.moe card-detail",
        "lookup_strategy": "detail_by_source_ids",
        "lookup": {},
        "expected_source_fields": ["pokemonAttr.attack[].text", "pokemonAttr.ability[].text"],
        "field_mapping": {
            "pokemonAttr.attack[].text": ["attacks[].effect_text_zh"],
            "pokemonAttr.ability[].text": ["abilities[].effect_text_zh"],
        },
        "desired_fields": ["attacks[].effect_text_zh", "abilities[].effect_text_zh"],
        "dry_run": True,
        "will_write_files": False,
        "network_enabled": False,
        "blocking_issues": [],
        "notes": [],
        **(overrides or {}),
    }


def _supporter_response(**overrides: object) -> dict:
    resp: dict = {
        "cardType": "Supporter",
        "description": "丢弃自己的手牌，抽出5张卡。",
    }
    resp.update(overrides)  # type: ignore[arg-type]
    return resp


def _fake_fetcher(response: dict):
    def _fetcher(_request: dict) -> dict:
        return response

    return _fetcher


# ---------------------------------------------------------------------------
# 1. Supporter description parse (top-level flat) + diagnostics
# ---------------------------------------------------------------------------


def test_supporter_description_parse():
    req = _supporter_dry_run_request()
    resp = _supporter_response()
    result = parse_tcg_mik_card_detail_response(resp, req)

    # text patch preview
    patch = result["normalized_patch_preview"]
    assert patch["text"]["rules_text_zh"] == "丢弃自己的手牌，抽出5张卡。"
    assert patch["text"]["trainer_text_zh"] == "丢弃自己的手牌，抽出5张卡。"
    assert patch["text"]["full_text_zh"] == "丢弃自己的手牌，抽出5张卡。"

    # classification
    assert patch["classification"]["card_supertype"] == "Trainer"
    assert patch["classification"]["trainer_subtype"] == "Supporter"

    # safety flags
    assert result["dry_run"] is True
    assert result["will_write_files"] is False
    assert result["errors"] == []
    assert result["raw_fields_found"] == ["cardType", "description"]

    # response_diagnostics
    diag = result["response_diagnostics"]
    assert diag["description_path"] == "$.description"
    assert diag["card_type_path"] == "$.cardType"
    assert diag["has_description"] is True
    assert diag["has_card_type"] is True
    assert diag["response_shape"] == "flat"
    assert "top_level_keys" in diag
    assert "candidate_paths_checked" in diag
    assert "safe_preview" in diag


# ---------------------------------------------------------------------------
# 2. Missing description
# ---------------------------------------------------------------------------


def test_missing_description():
    req = _supporter_dry_run_request()
    resp = _supporter_response(description=None)
    result = parse_tcg_mik_card_detail_response(resp, req)

    assert "text" not in result["normalized_patch_preview"]
    assert "missing_description" in result["errors"]
    assert result["response_diagnostics"]["has_description"] is False


# ---------------------------------------------------------------------------
# 3. Unknown cardType
# ---------------------------------------------------------------------------


def test_unknown_card_type():
    req = _supporter_dry_run_request()
    resp = _supporter_response(cardType="UnknownXYZ")
    result = parse_tcg_mik_card_detail_response(resp, req)

    assert result["normalized_patch_preview"]["classification"]["card_supertype"] == "Unknown"
    assert "unknown_card_type" in result["warnings"]


# ---------------------------------------------------------------------------
# 4. Pokemon attack / ability text preview
# ---------------------------------------------------------------------------


def test_pokemon_attack_ability_preview():
    req = _pokemon_dry_run_request()
    resp = {
        "pokemonAttr": {
            "attack": [
                {"name": "火之尾", "text": "附加30点伤害。"},
                {"name": "火焰", "text": ""},
            ],
            "ability": [
                {"name": "加速", "text": "每个回合可以使用1次。"},
            ],
        },
    }
    result = parse_tcg_mik_card_detail_response(resp, req)
    patch = result["normalized_patch_preview"]

    assert len(patch["attacks"]) == 1  # second attack has empty text
    assert patch["attacks"][0]["name"] == "火之尾"
    assert patch["attacks"][0]["effect_text_zh"] == "附加30点伤害。"

    assert len(patch["abilities"]) == 1
    assert patch["abilities"][0]["name"] == "加速"
    assert patch["abilities"][0]["effect_text_zh"] == "每个回合可以使用1次。"


# ---------------------------------------------------------------------------
# 5. Network disabled default
# ---------------------------------------------------------------------------


def test_network_disabled_default():
    client = TcgMikRefetchClient()
    assert client.network_enabled is False

    req = _supporter_dry_run_request()
    result = client.fetch_detail_for_request(req)

    assert result["errors"] == ["network_disabled"]
    assert result["normalized_patch_preview"] == {}
    assert result["dry_run"] is True

    # blocked result should have diagnostics
    diag = result["response_diagnostics"]
    assert diag["response_shape"] == "blocked"


# ---------------------------------------------------------------------------
# 6. Fake fetcher path
# ---------------------------------------------------------------------------


def test_fake_fetcher_path():
    resp = _supporter_response()
    client = TcgMikRefetchClient(fetcher=_fake_fetcher(resp), network_enabled=True)
    req = _supporter_dry_run_request()
    result = client.fetch_detail_for_request(req)

    assert result["errors"] == []
    assert result["normalized_patch_preview"]["text"]["rules_text_zh"] == "丢弃自己的手牌，抽出5张卡。"
    assert result["normalized_patch_preview"]["classification"]["card_supertype"] == "Trainer"

    # should have response_diagnostics from real parse
    diag = result["response_diagnostics"]
    assert diag["response_shape"] == "flat"
    assert diag["has_description"] is True


# ---------------------------------------------------------------------------
# 7. No file writes / no dangerous imports
# ---------------------------------------------------------------------------


def test_no_file_writes():
    source = MODULE_PATH.read_text(encoding="utf-8")
    for pattern in _NO_WRITE_PATTERNS:
        assert pattern not in source, f"Found forbidden write pattern: {pattern}"


def test_no_network_imports():
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden = {"requests", "httpx", "aiohttp", "bs4", "urllib.request"}
    imported: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])

    assert forbidden.isdisjoint(imported)


# ---------------------------------------------------------------------------
# 8. Full dry-run chain (7D → 7E → 7F → 7G)
# ---------------------------------------------------------------------------


def test_full_dry_run_chain_twm145():
    from ptcg.data_sources.normalized_card_text import build_normalized_records
    from ptcg.data_sources.text_refetch_plan import build_text_refetch_plan
    from ptcg.data_sources.text_refetch_dry_run import build_refetch_dry_run_requests

    chinese_data = ROOT / "card_chinese_data.json"
    cache_data = ROOT / "card_data_cache.json"
    cards_root = ROOT / "ptcg" / "cards"

    records = build_normalized_records(chinese_data, cache_data, cards_root)
    plan = build_text_refetch_plan(records)
    dry_requests = build_refetch_dry_run_requests(plan)

    # find TWM-145
    twm_req = next(r for r in dry_requests if r["card_key"] == "TWM-145")

    # fake response
    resp = _supporter_response(
        description="将自己的手牌全部放回牌库并重洗。然后，从牌库上方抽出5张卡。",
        cardType="Supporter",
    )
    client = TcgMikRefetchClient(fetcher=_fake_fetcher(resp), network_enabled=True)
    result = client.fetch_detail_for_request(twm_req)

    assert result["dry_run"] is True
    assert result["will_write_files"] is False
    assert result["errors"] == []
    assert result["normalized_patch_preview"]["text"]["rules_text_zh"] is not None
    assert result["normalized_patch_preview"]["classification"]["card_supertype"] == "Trainer"


# ===========================================================================
# NEW: response diagnostics & parser hardening tests
# ===========================================================================


# ---------------------------------------------------------------------------
# 9. data wrapper
# ---------------------------------------------------------------------------


def test_data_wrapper():
    """Parser supports $.data.description / $.data.cardType."""
    req = _supporter_dry_run_request()
    resp = {
        "data": {
            "description": "丢弃自己的手牌，抽出5张卡。",
            "cardType": "Supporter",
        },
    }
    result = parse_tcg_mik_card_detail_response(resp, req)

    patch = result["normalized_patch_preview"]
    assert patch["text"]["rules_text_zh"] == "丢弃自己的手牌，抽出5张卡。"
    assert patch["classification"]["card_supertype"] == "Trainer"

    diag = result["response_diagnostics"]
    assert diag["description_path"] == "$.data.description"
    assert diag["card_type_path"] == "$.data.cardType"
    assert diag["has_description"] is True
    assert diag["has_card_type"] is True
    assert diag["response_shape"] == "wrapped_data"
    assert "data_keys" in diag["safe_preview"]


# ---------------------------------------------------------------------------
# 10. data.card wrapper
# ---------------------------------------------------------------------------


def test_data_card_wrapper():
    """Parser supports $.data.card.description / $.data.card.cardType."""
    req = _supporter_dry_run_request()
    resp = {
        "data": {
            "card": {
                "description": "将自己的手牌全部放回牌库并重洗。然后，从牌库上方抽出5张卡。",
                "cardType": "Supporter",
            },
        },
    }
    result = parse_tcg_mik_card_detail_response(resp, req)

    patch = result["normalized_patch_preview"]
    assert patch["text"]["rules_text_zh"] is not None
    assert patch["classification"]["card_supertype"] == "Trainer"

    diag = result["response_diagnostics"]
    assert diag["description_path"] == "$.data.card.description"
    assert diag["card_type_path"] == "$.data.card.cardType"
    assert diag["response_shape"] == "wrapped_data_card"
    assert "card_keys" in diag["safe_preview"]


# ---------------------------------------------------------------------------
# 11. card wrapper
# ---------------------------------------------------------------------------


def test_card_wrapper():
    """Parser supports $.card.description / $.card.cardType."""
    req = _supporter_dry_run_request()
    resp = {
        "card": {
            "description": "支援者卡。",
            "cardType": "Supporter",
        },
    }
    result = parse_tcg_mik_card_detail_response(resp, req)

    patch = result["normalized_patch_preview"]
    assert patch["text"]["rules_text_zh"] == "支援者卡。"
    assert patch["classification"]["card_supertype"] == "Trainer"

    diag = result["response_diagnostics"]
    assert diag["description_path"] == "$.card.description"
    assert diag["card_type_path"] == "$.card.cardType"
    assert diag["response_shape"] == "wrapped_card"


# ---------------------------------------------------------------------------
# 12. result wrapper
# ---------------------------------------------------------------------------


def test_result_wrapper():
    """Parser supports $.result.description / $.result.cardType."""
    req = _supporter_dry_run_request()
    resp = {
        "result": {
            "description": "道具卡。",
            "cardType": "Item",
        },
    }
    result = parse_tcg_mik_card_detail_response(resp, req)

    patch = result["normalized_patch_preview"]
    assert patch["text"]["rules_text_zh"] == "道具卡。"
    assert patch["classification"]["card_supertype"] == "Trainer"
    assert patch["classification"]["trainer_subtype"] == "Item"

    diag = result["response_diagnostics"]
    assert diag["description_path"] == "$.result.description"
    assert diag["card_type_path"] == "$.result.cardType"
    assert diag["response_shape"] == "wrapped_result"


# ---------------------------------------------------------------------------
# 13. missing cardType (description present, cardType absent)
# ---------------------------------------------------------------------------


def test_missing_card_type_warning():
    """description exists but cardType is missing → warning missing_card_type."""
    req = _supporter_dry_run_request()
    resp = {"description": "道具卡效果文本。"}
    result = parse_tcg_mik_card_detail_response(resp, req)

    # text patch should still be generated
    patch = result["normalized_patch_preview"]
    assert patch["text"]["rules_text_zh"] == "道具卡效果文本。"

    # classification should be absent
    assert "classification" not in patch

    # warning should include missing_card_type
    assert "missing_card_type" in result["warnings"]

    # diagnostics: cardType not found
    diag = result["response_diagnostics"]
    assert diag["has_card_type"] is False
    assert diag["card_type_path"] is None
    assert diag["has_description"] is True


# ---------------------------------------------------------------------------
# 14. API error shape
# ---------------------------------------------------------------------------


def test_api_error_shape():
    """API returns {code: 404, message: 'not found'} → no crash, safe_preview captures."""
    req = _supporter_dry_run_request()
    resp = {"code": 404, "message": "not found"}
    result = parse_tcg_mik_card_detail_response(resp, req)

    # should not crash
    assert "missing_description" in result["errors"]
    assert "missing_card_type" in result["warnings"]

    diag = result["response_diagnostics"]
    assert diag["safe_preview"]["code"] == 404
    assert diag["safe_preview"]["message"] == "not found"
    assert diag["has_description"] is False
    assert diag["has_card_type"] is False
    assert diag["response_shape"] == "unknown"


# ---------------------------------------------------------------------------
# 15. invalid response shape (None)
# ---------------------------------------------------------------------------


def test_invalid_response_none():
    """Response is None → invalid_response_shape, no crash."""
    req = _supporter_dry_run_request()
    result = parse_tcg_mik_card_detail_response(None, req)

    assert "invalid_response_shape" in result["errors"]
    assert result["normalized_patch_preview"] == {}

    diag = result["response_diagnostics"]
    assert diag["response_shape"] == "invalid"
    assert diag["safe_preview"]["type"] == "NoneType"


# ---------------------------------------------------------------------------
# 16. invalid response shape (list)
# ---------------------------------------------------------------------------


def test_invalid_response_list():
    """Response is a list → invalid_response_shape, no crash."""
    req = _supporter_dry_run_request()
    result = parse_tcg_mik_card_detail_response([1, 2, 3], req)

    assert "invalid_response_shape" in result["errors"]
    diag = result["response_diagnostics"]
    assert diag["response_shape"] == "invalid"
    assert diag["safe_preview"]["type"] == "list"


# ---------------------------------------------------------------------------
# 17. safe_preview does not leak full raw response
# ---------------------------------------------------------------------------


def test_safe_preview_no_leak():
    """safe_preview must NOT include large fields like image, html, giant_text."""
    req = _supporter_dry_run_request()
    resp = {
        "description": "正常效果文本。",
        "cardType": "Supporter",
        "image": "data:image/png;base64,AAAA...(10MB fake image data)...",
        "html": "<div>very long html content ...</div>",
        "giant_text": "x" * 100000,
        "giantText": "y" * 100000,
        "cardImage": "https://example.com/huge-image.png",
        "fullCard": {"name": "full card JSON here"},
        "raw": b"binary data",
    }
    result = parse_tcg_mik_card_detail_response(resp, req)

    diag = result["response_diagnostics"]
    safe = diag["safe_preview"]

    # None of the blocked keys should appear in safe_preview
    blocked = {"image", "html", "giant_text", "giantText", "cardImage", "card_image", "raw", "fullCard"}
    for _k in safe:
        assert _k not in blocked, f"safe_preview leaked blocked key: {_k}"

    # But top_level_keys should include them (structural info is ok)
    assert "image" in diag["top_level_keys"]
    assert "html" in diag["top_level_keys"]

    # The giant text should NOT be present in safe_preview value
    safe_json_str = str(safe)
    assert "x" * 1000 not in safe_json_str  # giant_text content must not leak


# ---------------------------------------------------------------------------
# 18. Full dry-run chain with wrapped response
# ---------------------------------------------------------------------------


def test_full_dry_run_chain_with_data_wrapper():
    """7D→7E→7F→7G chain with data-wrapped fake response for TWM-145."""
    from ptcg.data_sources.normalized_card_text import build_normalized_records
    from ptcg.data_sources.text_refetch_plan import build_text_refetch_plan
    from ptcg.data_sources.text_refetch_dry_run import build_refetch_dry_run_requests

    chinese_data = ROOT / "card_chinese_data.json"
    cache_data = ROOT / "card_data_cache.json"
    cards_root = ROOT / "ptcg" / "cards"

    records = build_normalized_records(chinese_data, cache_data, cards_root)
    plan = build_text_refetch_plan(records)
    dry_requests = build_refetch_dry_run_requests(plan)

    twm_req = next(r for r in dry_requests if r["card_key"] == "TWM-145")

    # data-wrapped response
    resp = {
        "data": {
            "description": "将自己的手牌全部放回牌库并重洗。然后，从牌库上方抽出5张卡。",
            "cardType": "Supporter",
        },
    }
    client = TcgMikRefetchClient(fetcher=_fake_fetcher(resp), network_enabled=True)
    result = client.fetch_detail_for_request(twm_req)

    assert result["errors"] == []
    patch = result["normalized_patch_preview"]
    assert "text" in patch
    assert "classification" in patch
    assert patch["classification"]["card_supertype"] == "Trainer"

    diag = result["response_diagnostics"]
    assert diag["response_shape"] == "wrapped_data"
    assert diag["description_path"] == "$.data.description"
