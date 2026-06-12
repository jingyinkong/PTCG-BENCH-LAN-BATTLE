import ast
from pathlib import Path

from ptcg.data_sources.normalized_card_text import build_normalized_records


ROOT = Path(__file__).resolve().parents[2]
CHINESE_DATA = ROOT / "card_chinese_data.json"
CACHE_DATA = ROOT / "card_data_cache.json"
CARDS_ROOT = ROOT / "ptcg" / "cards"
MODULE_PATH = ROOT / "ptcg" / "data_sources" / "normalized_card_text.py"


def _build_records():
    return build_normalized_records(
        chinese_data_path=CHINESE_DATA,
        card_data_cache_path=CACHE_DATA,
        cards_root=CARDS_ROOT,
    )


def test_supporter_records_use_local_classification_and_require_text_refetch():
    records = _build_records()

    expected = {
        "TWM-145": ("ptcg/cards/TWM/twm145carmine.py", "TWM145Carmine"),
        "SSH-178": ("ptcg/cards/SSH/ssh178professorsresearch.py", "SSH178ProfessorsResearch"),
        "PAL-185": ("ptcg/cards/PAL/pal185iono.py", "PAL185Iono"),
    }

    for card_key, (local_file, class_name) in expected.items():
        record = records[card_key]

        assert record["card_key"] == card_key
        assert record["identity"]["card_key"] == card_key
        assert record["identity"]["local_file"] == local_file
        assert record["identity"]["local_class_name"] == class_name

        assert record["classification"]["card_supertype"] == "Trainer"
        assert record["classification"]["trainer_subtype"] == "Supporter"
        assert record["classification"]["classification_source"] == "local_class"
        assert record["classification"]["classification_confidence"] == "high"
        assert "card_data_cache.card_type_untrusted" in record["classification"]["classification_warnings"]

        assert record["quality_flags"]["untrusted_card_type"] is True
        assert record["quality_flags"]["missing_rules_text"] is True
        assert record["quality_flags"]["needs_text_refetch"] is True
        assert record["quality_flags"]["prompt_ready"] is False
        assert record["text"]["text_available"] is False
        assert record["text"]["text_quality"] == "missing"
        assert record["text"]["rules_text_zh"] is None
        assert record["text"]["trainer_text_zh"] is None


def test_cache_type_is_not_trusted_when_local_supporter_class_conflicts():
    records = _build_records()

    for card_key in ("TWM-145", "SSH-178", "PAL-185"):
        record = records[card_key]
        assert record["classification"]["card_supertype"] == "Trainer"
        assert record["quality_flags"]["untrusted_card_type"] is True
        assert "card_type_conflict" in record["classification"]["classification_warnings"]
        assert record["quality_flags"]["needs_type_refetch"] is False


def test_record_shape_is_stable_for_phase_7d_loader():
    records = _build_records()
    record = records["TWM-145"]

    assert set(record) == {
        "card_key",
        "identity",
        "classification",
        "text",
        "attacks",
        "abilities",
        "quality_flags",
        "provenance",
        "meta",
    }
    assert set(record["quality_flags"]) == {
        "missing_rules_text",
        "untrusted_card_type",
        "missing_local_file",
        "ambiguous_mapping",
        "needs_text_refetch",
        "needs_type_refetch",
        "unsupported_for_prompt",
        "prompt_ready",
        "missing_effect_text",
    }
    assert set(record["provenance"]) == {"sources", "field_source_map"}
    assert set(record["meta"]) == {"schema_version", "generator_version"}


def test_loader_module_has_no_network_imports():
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
