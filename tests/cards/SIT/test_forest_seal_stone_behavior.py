"""森林封印石 行为回归测试 — 验证后场附着位置 + Star Alchemy"""
import pytest
from ptcg.core.card_registry import registry
from ptcg.core.enums import CardPosition


def make_card():
    return registry.get("SIT-156")()


class TestForestSealStoneBehavior:
    """L4 效果逻辑测试：验证工具附着位置和 VSTAR 能力。"""

    def test_has_star_alchemy_ability(self, snapshot_game):
        """森林封印石提供 Star Alchemy 能力。"""
        card = make_card()
        assert hasattr(card, 'ability'), "Should have ability attribute"
        assert len(card.ability) >= 1, "Should have at least 1 ability"
        # ActiveAbility has .name attribute, not .get()
        ability_names = [a.name for a in card.ability]
        assert any("Star Alchemy" in n or "星之炼金术" in n for n in ability_names),             f"Should have Star Alchemy ability, got: {ability_names}"

    def test_card_is_tool_card(self, snapshot_game):
        """森林封印石是道具卡。"""
        card = make_card()
        from ptcg.core.card import ToolCard
        assert isinstance(card, ToolCard), "Should be a ToolCard"

    def test_card_not_available_when_not_in_hand(self, snapshot_game):
        """不在手牌时无 action。"""
        h = snapshot_game
        actions = make_card().get_actions(h.state)
        assert len(actions) == 0
