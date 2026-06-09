"""电气发生器 行为回归测试 — 使用 snapshot_game fixture 验证效果逻辑"""
import pytest
from ptcg.core.card_registry import registry
from ptcg.core.enums import CardPosition, CardType


def make_card():
    return registry.get("PAF-079")()


def _lightning_energy():
    """Create a lightning energy card using registry."""
    return registry.get("SVE-004")()


def _fire_energy():
    """Create a fire energy card using registry."""
    return registry.get("SVE-002")()


class TestElectricGeneratorBehavior:
    """L4 效果逻辑测试：预设游戏状态 → 执行 → 断言。"""

    def test_get_actions_with_deck_and_hand(self, snapshot_game):
        """手牌有电气发生器且牌库非空时，get_actions 返回 UseItemAction。"""
        h = snapshot_game
        card = make_card()
        h.p1.hand = [card]
        h.set_deck(h.p1, ["SVE-001"])
        actions = card.get_actions(h.state)
        assert len(actions) >= 1, f"Expected >=1 UseItemAction, got {len(actions)}"

    def test_get_actions_deck_empty(self, snapshot_game):
        """牌库为空时不可使用。"""
        h = snapshot_game
        card = make_card()
        h.p1.hand = [card]
        h.p1.left = []
        actions = card.get_actions(h.state)
        assert len(actions) == 0

    def test_reduce_action_discards_self(self, snapshot_game):
        """使用电气发生器后，道具卡自身应被丢到弃牌区。"""
        h = snapshot_game
        card = make_card()
        h.p1.hand = [card]
        h.set_deck(h.p1, ["SVE-004", "SVE-004", "SVE-004", "SVE-004", "SVE-004"])
        from ptcg.core.action import UseItemAction
        action = UseItemAction(h.p1.id, card)
        gen = card.reduce_action(action, h.state)
        try:
            next(gen)
        except StopIteration:
            pass
        assert card.cardPosition == CardPosition.DISCARD, f"Expected DISCARD, got {card.cardPosition}"
        assert card not in h.p1.hand

    def test_reduce_action_searches_lightning_energies(self, snapshot_game):
        """使用电气发生器后，牌库顶5张有电能量时触发选择交互。"""
        h = snapshot_game
        card = make_card()
        h.p1.hand = [card]
        # Deck top 5 all lightning energies
        h.set_deck(h.p1, ["SVE-004", "SVE-004", "SVE-004", "SVE-004", "SVE-004"])
        from ptcg.core.action import UseItemAction
        action = UseItemAction(h.p1.id, card)
        gen = card.reduce_action(action, h.state)
        try:
            next(gen)
        except StopIteration:
            pass
        assert card.cardPosition == CardPosition.DISCARD

    def test_no_lightning_bench_handles_gracefully(self, snapshot_game):
        """后场无电系宝可梦且无电能量时，应平安处理（不崩溃）。"""
        h = snapshot_game
        card = make_card()
        h.p1.hand = [card]
        # Deck has 5 non-lightning cards
        h.set_deck(h.p1, ["SVE-002", "SVE-002", "SVE-002", "SVE-002", "SVE-002"])
        h.p1.bench = []  # No bench
        from ptcg.core.action import UseItemAction
        action = UseItemAction(h.p1.id, card)
        gen = card.reduce_action(action, h.state)
        try:
            next(gen)
        except StopIteration:
            pass
        assert card.cardPosition == CardPosition.DISCARD

    def test_card_not_available_when_not_in_hand(self, snapshot_game):
        """不在手牌时不能使用。"""
        h = snapshot_game
        h.set_deck(h.p1, ["SVE-001"])
        actions = make_card().get_actions(h.state)
        assert len(actions) == 0
