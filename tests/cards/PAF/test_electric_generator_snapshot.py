"""电气发生器 场景快照集成测试 — 使用 snapshot_game fixture"""
from ptcg.core.card_registry import registry


def make_card():
    return registry.get("PAF-079")()


class TestElectricGeneratorSnapshot:
    """使用 snapshot_game 的集成测试。"""

    def test_card_available_when_in_hand_and_deck_not_empty(self, snapshot_game):
        """验证手牌有卡且牌库非空时，get_actions 返回 action。"""
        h = snapshot_game
        card = make_card()
        h.set_deck(h.p1, ["SVE-001"])
        h.p1.hand = [card]
        actions = card.get_actions(h.state)
        assert len(actions) >= 1, f"Expected >=1 actions, got {len(actions)}"

    def test_card_not_available_when_deck_empty(self, snapshot_game):
        """验证牌库为空时不能使用。"""
        h = snapshot_game
        card = make_card()
        h.p1.hand = [card]
        h.p1.left = []
        actions = card.get_actions(h.state)
        assert len(actions) == 0

    def test_card_not_available_when_not_in_hand(self, snapshot_game):
        """验证不在手牌时不能使用。"""
        h = snapshot_game
        h.set_deck(h.p1, ["SVE-001"])
        actions = make_card().get_actions(h.state)
        assert len(actions) == 0
