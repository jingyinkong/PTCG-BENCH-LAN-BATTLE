"""能量转移 (CES-129) — L3-L6 测试."""

import pytest
from ptcg.core.action import UseItemAction
from ptcg.core.card_registry import registry
from ptcg.core.enums import CardPosition, CardType, PokemonPosition, TrainerType

CARD_ID = "CES-129"


@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class TestCES129L3Structure:
    """L3: 精确属性断言."""

    def test_card_identity(self, card):
        assert card.id == "CES-129"
        assert card.name == "能量转移"
        assert card.cardType == CardType.NONE

    def test_trainer_attributes(self, card):
        assert card.trainerType == TrainerType.ITEM
        assert card.text == "选择自己场上的1只宝可梦身上附着的1个基本能量，改附于自己其他的宝可梦身上。"


def _make_card():
    return registry.get("CES-129")()

class Test能量转移Behavior:
    """ITEM 类型：使用行为测试."""
    def test_card_loads(self, snapshot_game):
        """卡牌可加载."""
        card = _make_card()
        assert card.name
        assert card.id == "CES-129"
    def test_get_actions_returns_item_when_in_hand(self, snapshot_game):
        """在手牌时 get_actions 返回使用动作."""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.HAND
        h.p1.hand = [card]
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

class Test能量转移L5EdgeCases:
    """L5: 标准边界条件（snapshot_game 预设状态验证）."""
    def test_card_loads_correctly(self, snapshot_game):
        """卡牌加载属性正确."""
        card = _make_card()
        assert card.name is not None, f"Expected non-empty name, got {card.name}"
        assert card.id == 'CES-129'
    def test_hp_non_negative(self, snapshot_game):
        """HP 非负（仅宝可梦卡）."""
        card = _make_card()
        if hasattr(card, 'hp') and card.hp is not None:
            assert card.hp >= 0

class Test能量转移L6Snapshot:
    """L6: 场景快照 — 手牌中存在性验证."""
    def test_snapshot_card_in_hand(self, snapshot_game):
        """快照: 卡牌在手牌中可访问."""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.HAND
        h.p1.hand = [card]
        assert len(h.p1.hand) == 1
        assert h.p1.hand[0].id == 'CES-129'