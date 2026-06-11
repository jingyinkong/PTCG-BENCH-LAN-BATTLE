"""verify_card_consistency.py 的单元测试."""
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from verify_card_consistency import (
    _CACHE_TYPE_MAP, _COST_MAP,
    _normalize_damage, _normalize_cost,
)


class TestNormalize:
    def test_damage_int(self):
        assert _normalize_damage(120) == 120

    def test_damage_dict(self):
        assert _normalize_damage({"amount": 80, "suffix": "+"}) == 80

    def test_damage_none(self):
        assert _normalize_damage(None) is None

    def test_damage_string(self):
        assert _normalize_damage("90") == 90

    def test_cost_cache_letters(self):
        assert _normalize_cost(["C", "C"]) == ["COLORLESS", "COLORLESS"]
        assert _normalize_cost(["R", "W"]) == ["FIRE", "WATER"]

    def test_cost_enum_names(self):
        from ptcg.core.enums import CardType
        cost = [CardType.FIRE, CardType.COLORLESS]
        assert _normalize_cost(cost) == ["FIRE", "COLORLESS"]


class TestTypeMapping:
    def test_cache_type_map(self):
        assert _CACHE_TYPE_MAP["Pokemon"] == "POKEMON"
        assert _CACHE_TYPE_MAP["Trainer"] == "TRAINER"
        assert _CACHE_TYPE_MAP["Energy"] == "ENERGY"

    def test_cost_map_complete(self):
        assert set(_COST_MAP.keys()) == {"R","W","L","G","P","F","D","M","C"}


class TestIntegration:
    def test_pal185_no_error(self):
        """PAL-185 card_type 已在 Phase 2 修复，不再有 ERROR。"""
        from verify_card_consistency import run_consistency_check
        report = run_consistency_check(["PAL-185"])
        errors = report["by_severity"].get("ERROR", [])
        super_type_errors = [e for e in errors if e["field"] == "super_type"]
        assert len(super_type_errors) == 0

    def test_asr133_no_error(self):
        from verify_card_consistency import run_consistency_check
        report = run_consistency_check(["ASR-133"])
        errors = report["by_severity"].get("ERROR", [])
        assert len(errors) == 0

    def test_full_run_valid_structure(self):
        from verify_card_consistency import run_consistency_check
        report = run_consistency_check(["PAL-185", "ASR-133"])
        assert "summary" in report
        assert "by_card" in report
        assert "by_severity" in report
        assert report["summary"]["total"] == 2
