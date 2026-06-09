"""Battle log (战斗日志) 测试"""
import json
import os
import pytest
from ptcg.core.deck import Deck
from ptcg.core.enums import PlayerId
from ptcg.core.recorder import GameRecorder
from ptcg.core.state import State
from ptcg.core.player import Player


def make_deck(card_ids=None):
    """Create a minimal Deck for testing."""
    from ptcg.core.card_registry import registry
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


class TestBattleLogRecording:
    def test_recorder_saves_and_loads(self, tmp_path):
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
        assert len(events) == 2
        assert events[0]["type"] == "game_start"
        assert events[1]["type"] == "termination"

    def test_state_dict_includes_both_players(self):
        deck = make_deck()
        p1, p2 = Player(deck), Player(deck)
        p1.id, p2.id = PlayerId.PLAYER1, PlayerId.PLAYER2
        state = State(p1, p2)
        d = state.to_dict()
        assert "player1" in d
        assert "player2" in d

    def test_choose_card_prompt_recorded(self, tmp_path):
        recorder = GameRecorder(seed=2, output_dir=str(tmp_path), auto_save=False)
        recorder.record_choose_card_prompt(1, 3, ["Card A", "Card B"], tips="Choose")
        deck = make_deck()
        p1, p2 = Player(deck), Player(deck)
        p1.id, p2.id = PlayerId.PLAYER1, PlayerId.PLAYER2
        state = State(p1, p2)
        recorder.record_termination(PlayerId.PLAYER1)
        events = GameRecorder.load(recorder.save())
        assert any(e["type"] == "choose_card_prompt" for e in events)
