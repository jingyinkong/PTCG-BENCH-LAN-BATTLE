"""场景快照测试框架验证"""
import pytest


class TestSnapshotGameFixture:
    def test_fixture_loads(self, snapshot_game):
        """验证 snapshot_game fixture 能正常初始化。"""
        assert snapshot_game.p1 is not None
        assert snapshot_game.p2 is not None
        assert snapshot_game.state is not None

    def test_set_hand(self, snapshot_game):
        """验证 set_hand 能正确设置手牌。"""
        snapshot_game.set_hand(snapshot_game.p1, ["SVE-001", "SVE-002"])
        snapshot_game.assert_hand_count(snapshot_game.p1, 2)

    def test_set_bench(self, snapshot_game):
        """验证 set_bench 能正确设置后场。"""
        snapshot_game.set_bench(snapshot_game.p1, ["ASR-113", "ASR-114"])
        snapshot_game.assert_bench_count(snapshot_game.p1, 2)

    def test_set_deck(self, snapshot_game):
        """验证 set_deck 能正确设置牌库。"""
        snapshot_game.set_deck(snapshot_game.p1, ["SVE-001", "SVE-002", "SVE-003"])
        snapshot_game.assert_deck_count(snapshot_game.p1, 3)

    def test_empty_initial_state(self, snapshot_game):
        """验证初始状态手牌和后场为空。"""
        snapshot_game.assert_hand_count(snapshot_game.p1, 0)
        snapshot_game.assert_bench_count(snapshot_game.p1, 0)
        snapshot_game.assert_deck_count(snapshot_game.p1, 0)

    def test_set_active(self, snapshot_game):
        """验证 set_active 能正确设置出战宝可梦。"""
        snapshot_game.set_active(snapshot_game.p1, "ASR-113")
        assert snapshot_game.p1.active is not None

    def test_full_snapshot_scenario(self, snapshot_game):
        """验证完整快照场景：手牌+后场+牌库+出战宝可梦。"""
        h = snapshot_game
        h.set_active(h.p1, "ASR-113")
        h.set_bench(h.p1, ["ASR-114"])
        h.set_hand(h.p1, ["SVE-001", "PAF-079"])
        h.set_deck(h.p1, ["SVE-002", "SVE-003", "SVE-004"])
        h.assert_hand_count(h.p1, 2)
        h.assert_bench_count(h.p1, 1)
        h.assert_deck_count(h.p1, 3)
