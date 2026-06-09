"""Auto-generated test skeleton for 喷火龙ex (OBF-125).

Fill in the TODOs with actual game state setup and assertions.
"""
import pytest
from ptcg.core.card_registry import registry


def make_card():
    c = registry.get("OBF-125")
    if c is None:
        pytest.skip("OBF-125 not registered")
    return c()


class Test喷火龙exSpecRules:
    def test_text_rules_present(self):
        card = make_card()
        # Rule: 特性 烈炎支配: 手牌从手牌打出附着能量时额外多附着1张基本火能量
        # Rule: 攻击 燃烧黑暗: 造成180伤害，对方出战宝可梦每次获得奖品卡数量x30额外伤害
        # Rule: 撤退费用2
        # Rule: ex规则：被击倒时对方拿2张奖品卡
        assert getattr(card, "text", None) or getattr(card, "name", None)  # Card has effect text

class Test喷火龙exSpecScenarios:
    @pytest.mark.skip(reason="Auto-generated skeleton — needs manual setup")
    def test_特性触发_手牌附火能量(self, snapshot_game):
        """特性触发：手牌附火能量"""
        h = snapshot_game
        card = make_card()
        # Expected: extra_fire_energy_attached = 1
        # TODO: h.set_hand(...), set_deck(...), execute action, assert

    @pytest.mark.skip(reason="Auto-generated skeleton — needs manual setup")
    def test_攻击伤害_对手0奖品(self, snapshot_game):
        """攻击伤害：对手0奖品"""
        h = snapshot_game
        card = make_card()
        # Expected: damage = 180
        # TODO: h.set_hand(...), set_deck(...), execute action, assert

    @pytest.mark.skip(reason="Auto-generated skeleton — needs manual setup")
    def test_攻击伤害_对手取过2奖品(self, snapshot_game):
        """攻击伤害：对手取过2奖品"""
        h = snapshot_game
        card = make_card()
        # Expected: damage = 240
        # TODO: h.set_hand(...), set_deck(...), execute action, assert

