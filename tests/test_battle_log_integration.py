"""战斗日志集成测试 — 验证双人日志可见性"""
import os
import pytest
from ptcg.core.deck import Deck
from ptcg.core.enums import PlayerId
from ptcg.core.recorder import GameRecorder
from ptcg.core.state import State
from ptcg.core.player import Player
from ptcg.core.card_registry import registry


def make_deck(card_ids=None):
    registry._ensure_loaded()
    if card_ids is None:
        card_ids = ["SVE-001", "SVE-002", "SVE-003", "SVE-004",
                     "SVE-005", "SVE-006", "SVE-007", "SVE-008"]
    cards = []
    for cid in card_ids:
        card_cls = registry.get(cid)
        if card_cls:
            cards.append(card_cls())
    return Deck(cards)


class TestBattleLogIntegration:
    """集成测试：战斗日志对双方玩家可见。"""

    def test_state_dict_includes_both_players(self):
        """state.to_dict() 包含 player1 和 player2 的数据。"""
        deck = make_deck()
        p1, p2 = Player(deck), Player(deck)
        p1.id, p2.id = PlayerId.PLAYER1, PlayerId.PLAYER2
        state = State(p1, p2)
        d = state.to_dict()
        assert "player1" in d, "state dict should have player1"
        assert "player2" in d, "state dict should have player2"

    def test_recorder_saves_events(self, tmp_path):
        """对局记录保存后，JSONL 文件存在且包含事件。"""
        recorder = GameRecorder(seed=1, output_dir=str(tmp_path), auto_save=False)
        deck = make_deck()
        p1, p2 = Player(deck), Player(deck)
        p1.id, p2.id = PlayerId.PLAYER1, PlayerId.PLAYER2
        state = State(p1, p2)
        recorder.record_game_start("player1", state)
        recorder.record_termination(PlayerId.PLAYER1)
        filepath = recorder.save()
        assert os.path.exists(filepath)
        events = GameRecorder.load(filepath)
        assert len(events) >= 2
        assert events[0]["type"] == "game_start"
        assert events[-1]["type"] == "termination"

    def test_choose_card_prompt_recorded(self, tmp_path):
        """choose_card_prompt 事件被记录到日志。"""
        recorder = GameRecorder(seed=2, output_dir=str(tmp_path), auto_save=False)
        recorder.record_choose_card_prompt(1, 3, ["Card A", "Card B"], tips="Choose")
        deck = make_deck()
        p1, p2 = Player(deck), Player(deck)
        p1.id, p2.id = PlayerId.PLAYER1, PlayerId.PLAYER2
        state = State(p1, p2)
        recorder.record_termination(PlayerId.PLAYER1)
        events = GameRecorder.load(recorder.save())
        assert any(e["type"] == "choose_card_prompt" for e in events),             "Log should contain choose_card_prompt events"

    def test_full_game_log_saves(self, tmp_path):
        """完整对局日志保存后文件可读取。"""
        recorder = GameRecorder(seed=42, output_dir=str(tmp_path), auto_save=False)
        deck = make_deck()
        p1, p2 = Player(deck), Player(deck)
        p1.id, p2.id = PlayerId.PLAYER1, PlayerId.PLAYER2
        state = State(p1, p2)
        recorder.record_game_start("test_user", state)
        recorder.record_termination(PlayerId.PLAYER1)
        filepath = recorder.save()
        assert filepath.endswith('.jsonl')
        events = GameRecorder.load(filepath)
        assert len(events) == 2
