"""Integration tests for AI vs AI battle testing framework."""

import sys
from pathlib import Path

import pytest

# Ensure backend is importable
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

pytestmark = pytest.mark.integration


class TestDatabaseMigration:
    def test_tables_exist(self):
        from backend.database import init_db
        conn = init_db()
        tables = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        for t in ("users", "sessions", "match_records", "test_tasks",
                   "test_games", "detected_issues", "cost_records"):
            assert t in tables, f"Missing table: {t}"
        conn.close()

    def test_users_has_is_admin(self):
        from backend.database import init_db
        conn = init_db()
        cols = {c[1] for c in conn.execute("PRAGMA table_info(users)").fetchall()}
        assert "is_admin" in cols
        conn.close()

    def test_user_version_is_2(self):
        from backend.database import init_db
        conn = init_db()
        v = conn.execute("PRAGMA user_version").fetchone()[0]
        assert v == 2
        conn.close()


class TestAuthExtension:
    def test_user_info_has_is_admin(self):
        from backend.auth import UserInfo
        u = UserInfo(id=1, username="test", is_admin=True, created_at="2024-01-01")
        assert u.is_admin is True

    def test_user_info_default_is_admin(self):
        from backend.auth import UserInfo
        u = UserInfo(id=1, username="test", created_at="2024-01-01")
        assert u.is_admin is False


class TestIssueDetector:
    def test_enhanced_checker_imports(self):
        from ptcg.utils.issue_detector import EnhancedStateChecker, IssueDetector
        assert EnhancedStateChecker() is not None

    def test_detect_softlock(self):
        from ptcg.utils.issue_detector import IssueDetector
        d = IssueDetector()
        findings = d.detect_all(steps=60, damage_history=[0]*25,
                                llm_failures=0, cards_involved=set(), winner=None)
        assert any(f["category"] == "softlock" for f in findings)

    def test_detect_llm_anomaly(self):
        from ptcg.utils.issue_detector import IssueDetector
        d = IssueDetector()
        findings = d.detect_all(steps=10, damage_history=[10],
                                llm_failures=5, cards_involved=set(), winner=None)
        assert any(f["category"] == "llm_anomaly" for f in findings)


class TestReplayChecker:
    def test_replay_checker_creates(self):
        from ptcg.utils.replay_checker import ReplayChecker
        rc = ReplayChecker(seed=42)
        assert rc.seed == 42


class TestAPIRouters:
    def test_routes_registered(self):
        from backend.deck_manager import router as d
        from backend.test_runner import router as t
        from backend.issue_reporter import router as i
        from backend.cost_tracker import router as c
        assert any("/api/decks" in str(r.path) for r in d.routes)
        assert any("/api/test/run" in str(r.path) for r in t.routes)
        assert any("/api/test/issues" in str(r.path) for r in i.routes)
        assert any("/api/test/cost" in str(r.path) for r in c.routes)


class TestPokemonTCGEnhancedCheck:
    def test_enable_enhanced_check_param(self):
        from ptcg.core.envs import PokemonTCG
        env = PokemonTCG(seed=0, enable_enhanced_check=True)
        assert env.enable_enhanced_check is True

    def test_default_enhanced_check_is_false(self):
        from ptcg.core.envs import PokemonTCG
        env = PokemonTCG(seed=0)
        assert env.enable_enhanced_check is False
