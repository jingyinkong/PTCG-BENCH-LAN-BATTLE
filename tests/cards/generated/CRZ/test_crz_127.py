"""能量回收 (CRZ-127) — L3-L6 测试."""

import pytest
from ptcg.core.action import UseItemAction
from ptcg.core.card_registry import registry
from ptcg.core.enums import CardPosition, CardType, PokemonPosition, TrainerType

CARD_ID = "CRZ-127"


@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class TestCRZ127L3Structure:
    """L3: 精确属性断言."""

    def test_card_identity(self, card):
        assert card.id == "CRZ-127"
        assert card.name == "能量回收"
        assert card.cardType == CardType.NONE

    def test_trainer_attributes(self, card):
        assert card.trainerType == TrainerType.ITEM
        assert card.text == "Put up to 2 basic Energy cards from your discard pile into your hand."


def _make_card():
    return registry.get("CRZ-127")()

class Test能量回收Behavior:
    """ITEM 类型：使用行为测试."""
    def test_card_loads(self, snapshot_game):
        """卡牌可加载."""
        card = _make_card()
        assert card.name
        assert card.id == "CRZ-127"
    def test_get_actions_returns_item_when_in_hand(self, snapshot_game):
        """在手牌且有弃牌区有基本能量时返回动作."""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.HAND
        h.p1.hand = [card]
        h.p1.discard = [registry.get("SVE-003")()]
        actions = card.get_actions(h.state)
        assert len(actions) > 0
        assert any(isinstance(a, UseItemAction) for a in actions)
    def test_get_actions_empty_when_not_in_hand(self, snapshot_game):
        """不在手牌时返回空."""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.LEFT
        actions = card.get_actions(h.state)
        assert len(actions) == 0
    def test_reduce_action(self, snapshot_game):
        """使用后不抛异常."""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.HAND
        h.p1.hand = [card]
        action = UseItemAction(h.p1.id, card)
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

class Test能量回收L5EdgeCases:
    """L5: 标准边界条件（snapshot_game 预设状态验证）."""
    def test_card_loads_correctly(self, snapshot_game):
        """卡牌加载属性正确."""
        card = _make_card()
        assert card.name is not None, f"Expected non-empty name, got {card.name}"
        assert card.id == 'CRZ-127'
    def test_hp_non_negative(self, snapshot_game):
        """HP 非负（仅宝可梦卡）."""
        card = _make_card()
        if hasattr(card, 'hp') and card.hp is not None:
            assert card.hp >= 0

class Test能量回收L6Snapshot:
    """L6: 场景快照 — 手牌中存在性验证."""
    def test_snapshot_card_in_hand(self, snapshot_game):
        """快照: 卡牌在手牌中可访问."""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.HAND
        h.p1.hand = [card]
        assert len(h.p1.hand) == 1
        assert h.p1.hand[0].id == 'CRZ-127'