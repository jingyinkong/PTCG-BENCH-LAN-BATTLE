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
# Supporter description parse
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


# ---------------------------------------------------------------------------
# Missing description
# ---------------------------------------------------------------------------


def test_missing_description():
    req = _supporter_dry_run_request()
    resp = _supporter_response(description=None)
    result = parse_tcg_mik_card_detail_response(resp, req)

    assert "text" not in result["normalized_patch_preview"]
    assert "missing_description" in result["errors"]


# ---------------------------------------------------------------------------
# Unknown cardType
# ---------------------------------------------------------------------------


def test_unknown_card_type():
    req = _supporter_dry_run_request()
    resp = _supporter_response(cardType="UnknownXYZ")
    result = parse_tcg_mik_card_detail_response(resp, req)

    assert result["normalized_patch_preview"]["classification"]["card_supertype"] == "Unknown"
    assert "unknown_card_type" in result["warnings"]


# ---------------------------------------------------------------------------
# Pokemon attack / ability text preview
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
# Network disabled default
# ---------------------------------------------------------------------------


def test_network_disabled_default():
    client = TcgMikRefetchClient()
    assert client.network_enabled is False

    req = _supporter_dry_run_request()
    result = client.fetch_detail_for_request(req)

    assert result["errors"] == ["network_disabled"]
    assert result["normalized_patch_preview"] == {}
    assert result["dry_run"] is True


# ---------------------------------------------------------------------------
# Fake fetcher path
# ---------------------------------------------------------------------------


def test_fake_fetcher_path():
    resp = _supporter_response()
    client = TcgMikRefetchClient(fetcher=_fake_fetcher(resp), network_enabled=True)
    req = _supporter_dry_run_request()
    result = client.fetch_detail_for_request(req)

    assert result["errors"] == []
    assert result["normalized_patch_preview"]["text"]["rules_text_zh"] == "丢弃自己的手牌，抽出5张卡。"
    assert result["normalized_patch_preview"]["classification"]["card_supertype"] == "Trainer"


# ---------------------------------------------------------------------------
# No file writes / no dangerous imports
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
# Full dry-run chain (7D → 7E → 7F → 7G)
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
