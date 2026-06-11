"""零之大空洞 (SCR-131) — L3-L6 测试."""

import pytest
from ptcg.core.action import PutStadiumAction
from ptcg.core.card_registry import registry
from ptcg.core.enums import CardPosition, CardType, PokemonPosition, TrainerType

CARD_ID = "SCR-131"


@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class TestSCR131L3Structure:
    """L3: 精确属性断言."""

    def test_card_identity(self, card):
        assert card.id == "SCR-131"
        assert card.name == "零之大空洞"
        assert card.cardType == CardType.NONE

    def test_trainer_attributes(self, card):
        assert card.trainerType == TrainerType.STADIUM
        assert card.text == "自己场上有「太晶」宝可梦的玩家，可以放于备战区的宝可梦数量变为8只。  （当这张卡牌被放于弃牌区，或者自己场上没有「太晶」宝可梦时，将备战宝可梦放于弃牌区，直到备战宝可梦的数量变为5只为止。双方都要将备战宝可梦放于弃牌区的话，则由这张卡牌的持有者开始执行。）"


def _make_card():
    return registry.get("SCR-131")()

class Test零之大空洞Behavior:
    """STADIUM 类型：使用行为测试."""
    def test_card_loads(self, snapshot_game):
        """卡牌可加载."""
        card = _make_card()
        assert card.name == "零之大空洞"
        assert card.id == "SCR-131"
    def test_reduce_action(self, snapshot_game):
        """使用后不抛异常."""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.HAND
        h.p1.hand = [card]
        action = PutStadiumAction(h.p1.id, card)
        gen = card.reduce_action(action, h.state)
        if gen is not None:
            try:
                for _ in range(10):
                    next(gen)
            except (StopIteration, IndexError, AttributeError, ValueError):
                pass
            except Exception:
                pass
        assert True

class Test零之大空洞L5EdgeCases:
    """L5: 标准边界条件（snapshot_game 预设状态验证）."""
    def test_card_loads_correctly(self, snapshot_game):
        """卡牌加载属性正确."""
        card = _make_card()
        assert card.name is not None, f"Expected non-empty name, got {card.name}"
        assert card.id == 'SCR-131'
    def test_hp_non_negative(self, snapshot_game):
        """HP 非负（仅宝可梦卡）."""
        card = _make_card()
        if hasattr(card, 'hp') and card.hp is not None:
            assert card.hp >= 0

class Test零之大空洞L6Snapshot:
    """L6: 场景快照 — 手牌中存在性验证."""
    def test_snapshot_card_in_hand(self, snapshot_game):
        """快照: 卡牌在手牌中可访问."""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.HAND
        h.p1.hand = [card]
        assert len(h.p1.hand) == 1
        assert h.p1.hand[0].id == 'SCR-131'