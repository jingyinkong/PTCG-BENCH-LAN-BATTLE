"""Auto-generated test skeleton for 森林封印石 (SIT-156).

Fill in the TODOs with actual game state setup and assertions.
"""
import pytest
from ptcg.core.card_registry import registry


def make_card():
    c = registry.get("SIT-156")
    if c is None:
        pytest.skip("SIT-156 not registered")
    return c()


class Test森林封印石SpecRules:
    def test_text_rules_present(self):
        card = make_card()
        # Rule: 附着于宝可梦V（前场或后场均可）
        # Rule: 被附着的宝可梦V可使用VSTAR能力 Star Alchemy
        # Rule: Star Alchemy: 从牌库搜索任意1张卡加入手牌并重洗
        # Rule: 每局游戏限用1次VSTAR能力
        # Rule: 宝可梦道具规则：每只宝可梦最多附着1张
        assert card.text  # Card has effect text

class Test森林封印石SpecScenarios:
    @pytest.mark.skip(reason="Auto-generated skeleton — needs manual setup")
    def test_后场附着_使用能力(self, snapshot_game):
        """后场附着+使用能力"""
        h = snapshot_game
        card = make_card()
        # Expected: attach_position = BENCH_ATTACHMENT
        # Expected: ability_usable = True
        # Expected: card_to_hand = 1
        # TODO: h.set_hand(...), set_deck(...), execute action, assert

    @pytest.mark.skip(reason="Auto-generated skeleton — needs manual setup")
    def test_前场附着_使用能力(self, snapshot_game):
        """前场附着+使用能力"""
        h = snapshot_game
        card = make_card()
        # Expected: attach_position = ACTIVE_ATTACHMENT
        # Expected: ability_usable = True
        # TODO: h.set_hand(...), set_deck(...), execute action, assert

    @pytest.mark.skip(reason="Auto-generated skeleton — needs manual setup")
    def test_边界_非V宝可梦不能使用能力(self, snapshot_game):
        """边界：非V宝可梦不能使用能力"""
        h = snapshot_game
        card = make_card()
        # Expected: ability_usable = False
        # TODO: h.set_hand(...), set_deck(...), execute action, assert

    @pytest.mark.skip(reason="Auto-generated skeleton — needs manual setup")
    def test_边界_VSTAR已用过后不能再用(self, snapshot_game):
        """边界：VSTAR已用过后不能再用"""
        h = snapshot_game
        card = make_card()
        # Expected: ability_usable = False
        # TODO: h.set_hand(...), set_deck(...), execute action, assert

