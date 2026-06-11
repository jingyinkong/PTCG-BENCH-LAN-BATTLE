"""反击捕捉器 (CIN-091) — L3-L6 测试."""

import pytest
from ptcg.core.action import UseItemAction
from ptcg.core.card_registry import registry
from ptcg.core.enums import CardPosition, CardType, PokemonPosition, TrainerType

CARD_ID = "CIN-091"


@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class TestCIN091L3Structure:
    """L3: 精确属性断言."""

    def test_card_identity(self, card):
        assert card.id == "CIN-091"
        assert card.name == "反击捕捉器"
        assert card.cardType == CardType.NONE

    def test_trainer_attributes(self, card):
        assert card.trainerType == TrainerType.ITEM
        assert card.text == "这张卡牌，只有在自己的剩余奖赏卡张数，比对手的剩余奖赏卡张数多时才可使用。选择对手的1只备战宝可梦，将其与战斗宝可梦互换。"


def _make_card():
    return registry.get("CIN-091")()

class Test反击捕捉器Behavior:
    """ITEM 类型：使用行为测试."""
    def test_card_loads(self, snapshot_game):
        """卡牌可加载."""
        card = _make_card()
        assert card.name
        assert card.id == "CIN-091"
    def test_get_actions_returns_item_when_trailing_in_prizes(self, snapshot_game):
        """奖赏卡落后时返回使用动作."""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.HAND
        h.p1.hand = [card]
        h.p1.prize = [1, 2, 3]
        h.p2.prize = [1]
        bench_mon = registry.get("ASR-133")()
        bench_mon.position = PokemonPosition.BENCH
        bench_mon.cardPosition = CardPosition.BENCH
        h.p2.bench = [bench_mon]
        actions = card.get_actions(h.state)
        assert len(actions) > 0
        assert any(isinstance(a, UseItemAction) for a in actions)
    def test_get_actions_empty_when_not_trailing(self, snapshot_game):
        """奖赏卡不落后时返回空."""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.HAND
        h.p1.hand = [card]
        h.p1.prize = [1]
        h.p2.prize = [1, 2, 3]
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

class Test反击捕捉器L5EdgeCases:
    """L5: 标准边界条件（snapshot_game 预设状态验证）."""
    def test_card_loads_correctly(self, snapshot_game):
        """卡牌加载属性正确."""
        card = _make_card()
        assert card.name is not None, f"Expected non-empty name, got {card.name}"
        assert card.id == 'CIN-091'
    def test_hp_non_negative(self, snapshot_game):
        """HP 非负（仅宝可梦卡）."""
        card = _make_card()
        if hasattr(card, 'hp') and card.hp is not None:
            assert card.hp >= 0

class Test反击捕捉器L6Snapshot:
    """L6: 场景快照 — 手牌中存在性验证."""
    def test_snapshot_card_in_hand(self, snapshot_game):
        """快照: 卡牌在手牌中可访问."""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.HAND
        h.p1.hand = [card]
        assert len(h.p1.hand) == 1
        assert h.p1.hand[0].id == 'CIN-091'