import ast
from pathlib import Path

from ptcg.data_sources.normalized_card_text import build_normalized_records
from ptcg.data_sources.text_refetch_plan import build_text_refetch_plan


ROOT = Path(__file__).resolve().parents[2]
CHINESE_DATA = ROOT / "card_chinese_data.json"
CACHE_DATA = ROOT / "card_data_cache.json"
CARDS_ROOT = ROOT / "ptcg" / "cards"
MODULE_PATH = ROOT / "ptcg" / "data_sources" / "text_refetch_plan.py"


def _build_records():
    return build_normalized_records(
        chinese_data_path=CHINESE_DATA,
        card_data_cache_path=CACHE_DATA,
        cards_root=CARDS_ROOT,
    )


def _fake_record(
    *,
    card_key: str,
    set_code: str | None = "TST",
    normalized_number: str | None = "1",
    name_en: str | None = "Test Card",
    name_zh: str | None = "Test Card",
    local_file: str | None = "ptcg/cards/TST/tst001testcard.py",
    card_supertype: str = "Trainer",
    trainer_subtype: str = "Supporter",
    missing_rules_text: bool = False,
    missing_effect_text: bool = False,
    needs_text_refetch: bool = False,
    needs_type_refetch: bool = False,
    prompt_ready: bool = False,
    untrusted_card_type: bool = False,
    missing_local_file: bool = False,
    ambiguous_mapping: bool = False,
    text_quality: str = "missing",
    derived_from_partial_sources: bool = False,
    source_ids: dict | None = None,
) -> dict:
    return {
        "card_key": card_key,
        "identity": {
            "card_key": card_key,
            "set_code": set_code,
            "normalized_number": normalized_number,
            "name_en": name_en,
            "name_zh": name_zh,
            "local_file": None if missing_local_file else local_file,
            "source_ids": source_ids or {},
        },
        "classification": {
            "card_supertype": card_supertype,
            "trainer_subtype": trainer_subtype,
            "pokemon_stage": None,
            "energy_type": None,
        },
        "text": {
            "text_quality": text_quality,
        },
        "quality_flags": {
            "missing_rules_text": missing_rules_text,
            "missing_effect_text": missing_effect_text,
            "needs_text_refetch": needs_text_refetch,
            "needs_type_refetch": needs_type_refetch,
            "prompt_ready": prompt_ready,
            "untrusted_card_type": untrusted_card_type,
            "missing_local_file": missing_local_file,
            "ambiguous_mapping": ambiguous_mapping,
            "derived_from_partial_sources": derived_from_partial_sources,
        },
    }


def _plan_by_key(plan: list[dict]) -> dict[str, dict]:
    return {item["card_key"]: item for item in plan}


def test_twm145_is_planned_as_p0_trainer_rules_refetch():
    records = _build_records()
    banned_output = ROOT / "data" / "normalized_card_text.json"
    existed_before = banned_output.exists()

    plan = build_text_refetch_plan(records)
    plan_by_key = _plan_by_key(plan)

    assert banned_output.exists() is existed_before
    assert "TWM-145" in plan_by_key
    assert plan_by_key["TWM-145"]["priority"] == "P0"
    assert "missing_rules_text" in plan_by_key["TWM-145"]["reasons"]
    assert "trainer_text_zh" in plan_by_key["TWM-145"]["desired_fields"]
    assert "rules_text_zh" in plan_by_key["TWM-145"]["desired_fields"]
    assert plan_by_key["TWM-145"]["dry_run"] is True


def test_ssh178_is_planned_as_supporter_with_refetch_locator():
    records = _build_records()

    plan = build_text_refetch_plan(records)
    plan_by_key = _plan_by_key(plan)
    item = plan_by_key["SSH-178"]

    assert item["priority"] == "P0"
    assert item["card_supertype"] == "Trainer"
    assert item["trainer_subtype"] == "Supporter"
    assert item["can_refetch"] is True or "needs_lookup_before_detail" in item["reasons"]


def test_pal185_keeps_prompt_not_ready_reason_and_desired_fields():
    records = _build_records()

    plan = build_text_refetch_plan(records)
    plan_by_key = _plan_by_key(plan)
    item = plan_by_key["PAL-185"]

    assert item["priority"] == "P0"
    assert "prompt_not_ready" in item["reasons"]
    assert item["desired_fields"]


def test_prompt_ready_record_without_refetch_needs_is_skipped():
    records = {
        "TST-1": _fake_record(
            card_key="TST-1",
            prompt_ready=True,
            needs_text_refetch=False,
            needs_type_refetch=False,
            missing_rules_text=False,
        )
    }

    assert build_text_refetch_plan(records) == []


def test_missing_locator_is_not_silently_swallowed():
    records = {
        "UNK-0": _fake_record(
            card_key="UNK-0",
            set_code=None,
            normalized_number=None,
            name_en=None,
            name_zh=None,
            local_file=None,
            card_supertype="Unknown",
            trainer_subtype="Unknown",
            missing_local_file=True,
            needs_text_refetch=True,
            prompt_ready=False,
        )
    }

    plan = build_text_refetch_plan(records)

    assert len(plan) == 1
    assert plan[0]["card_key"] == "UNK-0"
    assert plan[0]["can_refetch"] is False
    assert "missing_refetch_locator" in plan[0]["blocking_issues"]


def test_plan_module_has_no_network_imports():
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


def test_plan_order_is_stable_by_priority_supertype_and_card_key():
    records = {
        "B-2": _fake_record(
            card_key="B-2",
            missing_rules_text=True,
            needs_text_refetch=True,
            prompt_ready=False,
            source_ids={"set_code_cn": "AAA", "card_index_cn": "002"},
        ),
        "A-0": _fake_record(
            card_key="A-0",
            missing_rules_text=True,
            needs_text_refetch=True,
            prompt_ready=False,
            source_ids={"set_code_cn": "AAA", "card_index_cn": "001"},
        ),
        "A-1": _fake_record(
            card_key="A-1",
            card_supertype="Pokemon",
            trainer_subtype="Unknown",
            missing_effect_text=True,
            needs_text_refetch=True,
            prompt_ready=False,
            source_ids={"set_code_cn": "AAA", "card_index_cn": "003"},
        ),
        "C-3": _fake_record(
            card_key="C-3",
            card_supertype="Unknown",
            trainer_subtype="Unknown",
            text_quality="partial",
            derived_from_partial_sources=True,
            prompt_ready=False,
            source_ids={"set_code_cn": "AAA", "card_index_cn": "004"},
        ),
    }

    plan = build_text_refetch_plan(records)

    assert [item["card_key"] for item in plan] == ["A-0", "B-2", "A-1", "C-3"]
