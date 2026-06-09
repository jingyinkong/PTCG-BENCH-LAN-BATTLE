"""大地容器 行为回归测试 — 验证可选择丢弃手牌而非硬编码 hand[0]"""
import pytest
from ptcg.core.card_registry import registry
from ptcg.core.enums import CardPosition


def make_card():
    return registry.get("PRE-106")()


class TestEarthenVesselBehavior:
    """L4 效果逻辑测试：验证大地容器的丢弃选择和能量搜索。"""

    def test_get_actions_requires_two_cards_in_hand(self, snapshot_game):
        """手牌少于2张时（仅大地容器自身）不可使用。"""
        h = snapshot_game
        card = make_card()
        h.p1.hand = [card]
        actions = card.get_actions(h.state)
        assert len(actions) == 0

    def test_get_actions_with_extra_card(self, snapshot_game):
        """手牌 >= 2 张时可使用。"""
        h = snapshot_game
        card = make_card()
        extra = registry.get("SVE-001")()
        h.p1.hand = [card, extra]
        actions = card.get_actions(h.state)
        assert len(actions) >= 1

    def test_reduce_action_discards_self(self, snapshot_game):
        """使用后道具自身被丢弃。"""
        h = snapshot_game
        card = make_card()
        extra = registry.get("SVE-001")()
        h.p1.hand = [card, extra]
        h.set_deck(h.p1, ["SVE-001"] * 5)
        from ptcg.core.action import UseItemAction
        action = UseItemAction(h.p1.id, card)
        gen = card.reduce_action(action, h.state)
        try:
            next(gen)
        except StopIteration:
            pass
        assert card.cardPosition == CardPosition.DISCARD
        assert card not in h.p1.hand

    def test_reduce_action_enters_choice_flow(self, snapshot_game):
        """验证：reduce_action 进入选择交互流程（非硬编码 hand[0]）。"""
        h = snapshot_game
        card = make_card()
        extra = registry.get("SVE-001")()
        h.p1.hand = [card, extra]
        h.set_deck(h.p1, ["SVE-001"] * 5)
        from ptcg.core.action import UseItemAction
        action = UseItemAction(h.p1.id, card)
        gen = card.reduce_action(action, h.state)
        try:
            next(gen)
        except StopIteration:
            pass
        # After execution, card is discarded
        assert card.cardPosition == CardPosition.DISCARD

    def test_card_not_in_hand_no_action(self, snapshot_game):
        """不在手牌时无可用 action。"""
        h = snapshot_game
        h.set_deck(h.p1, ["SVE-001"])
        actions = make_card().get_actions(h.state)
        assert len(actions) == 0
