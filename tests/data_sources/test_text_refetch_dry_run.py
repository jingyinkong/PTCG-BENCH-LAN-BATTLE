import ast
from pathlib import Path

from ptcg.data_sources.normalized_card_text import build_normalized_records
from ptcg.data_sources.text_refetch_plan import build_text_refetch_plan
from ptcg.data_sources.text_refetch_dry_run import build_refetch_dry_run_requests

ROOT = Path(__file__).resolve().parents[2]
CHINESE_DATA = ROOT / "card_chinese_data.json"
CACHE_DATA = ROOT / "card_data_cache.json"
CARDS_ROOT = ROOT / "ptcg" / "cards"
MODULE_PATH = ROOT / "ptcg" / "data_sources" / "text_refetch_dry_run.py"

_NO_WRITE_PATTERNS = {
    "Path.write_text",
    "open(",
    'open(',
    "json.dump",
    ".write(",
}


def _build_dry_run():
    records = build_normalized_records(
        chinese_data_path=CHINESE_DATA,
        card_data_cache_path=CACHE_DATA,
        cards_root=CARDS_ROOT,
    )
    plan = build_text_refetch_plan(records)
    return build_refetch_dry_run_requests(plan)


def _by_key(requests: list[dict]) -> dict[str, dict]:
    return {req["card_key"]: req for req in requests}


def _fake_plan_item(
    *,
    card_key: str,
    name_en: str = "Test",
    name_zh: str = "Test",
    can_refetch: bool = True,
    desired_fields: list[str] | None = None,
    source_ids: dict | None = None,
    blocking_issues: list[str] | None = None,
) -> dict:
    return {
        "card_key": card_key,
        "name_en": name_en,
        "name_zh": name_zh,
        "can_refetch": can_refetch,
        "desired_fields": desired_fields or [],
        "source_ids": source_ids or {},
        "blocking_issues": blocking_issues or [],
    }


# ---- real-card tests ----

def test_twm145_dry_run_request():
    requests = _build_dry_run()
    by_key = _by_key(requests)

    req = by_key["TWM-145"]
    assert req["dry_run"] is True
    assert req["will_write_files"] is False
    assert req["network_enabled"] is False
    assert req["source"] == "tcg.mik.moe card-detail"
    assert "description" in req["field_mapping"]
    assert "text.rules_text_zh" in req["field_mapping"]["description"]
    assert "text.trainer_text_zh" in req["field_mapping"]["description"]
    assert "text.full_text_zh" in req["field_mapping"]["description"]


def test_ssh178_dry_run_request():
    requests = _build_dry_run()
    by_key = _by_key(requests)

    req = by_key["SSH-178"]
    assert "description" in req["expected_source_fields"]
    assert "cardType" in req["expected_source_fields"]
    assert "rules_text_zh" in req["desired_fields"]
    assert "trainer_text_zh" in req["desired_fields"]


def test_pal185_dry_run_request():
    requests = _build_dry_run()
    by_key = _by_key(requests)

    req = by_key["PAL-185"]
    assert req["lookup_strategy"] != "unavailable"
    assert req["blocking_issues"] == []
    assert req["can_refetch"] is True


# ---- construction tests ----

def test_missing_locator_produces_unavailable_strategy():
    items = [
        _fake_plan_item(
            card_key="UNK-0",
            can_refetch=False,
            source_ids={},
        )
    ]
    reqs = build_refetch_dry_run_requests(items)

    assert len(reqs) == 1
    assert reqs[0]["card_key"] == "UNK-0"
    assert reqs[0]["lookup_strategy"] == "unavailable"
    assert "missing_refetch_locator" in reqs[0]["blocking_issues"]
    assert reqs[0]["can_refetch"] is False
    assert reqs[0]["dry_run"] is True
    assert reqs[0]["will_write_files"] is False


def test_name_fallback_when_missing_set_number():
    items = [
        _fake_plan_item(
            card_key="NML-1",
            name_en="Some Card",
            source_ids={"card_data_cache_key": "XYZ"},
        )
    ]
    reqs = build_refetch_dry_run_requests(items)

    assert len(reqs) == 1
    assert reqs[0]["lookup_strategy"] == "search_then_detail_by_name"
    assert "name_lookup_may_be_ambiguous" in reqs[0]["notes"]


def test_search_then_detail_when_have_set_number_but_no_mik_ids():
    items = [
        _fake_plan_item(
            card_key="SET-1",
            source_ids={"card_data_cache_key": "TWM-145"},
        )
    ]
    reqs = build_refetch_dry_run_requests(items)

    assert len(reqs) == 1
    assert reqs[0]["lookup_strategy"] == "search_then_detail_by_set_number"
    assert "needs_lookup_before_detail" in reqs[0]["notes"]


# ---- safety tests ----

def test_dry_run_module_has_no_network_imports():
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden = {"requests", "httpx", "aiohttp", "bs4"}
    imported: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])

    assert forbidden.isdisjoint(imported)


def test_dry_run_module_does_not_write_files():
    source = MODULE_PATH.read_text(encoding="utf-8")
    for pattern in _NO_WRITE_PATTERNS:
        assert pattern not in source, f"Found forbidden write pattern: {pattern}"


def test_output_order_stable_matches_input_order():
    items = [
        _fake_plan_item(card_key="B-1", source_ids={"set_code_cn": "X", "card_index_cn": "1"}),
        _fake_plan_item(card_key="A-0", source_ids={"set_code_cn": "X", "card_index_cn": "0"}),
        _fake_plan_item(card_key="C-2", source_ids={"set_code_cn": "X", "card_index_cn": "2"}),
    ]
    reqs = build_refetch_dry_run_requests(items)
    assert [req["card_key"] for req in reqs] == ["B-1", "A-0", "C-2"]
