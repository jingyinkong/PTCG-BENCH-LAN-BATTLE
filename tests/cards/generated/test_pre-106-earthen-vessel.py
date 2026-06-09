"""Auto-generated test skeleton for 大地容器 (PRE-106).

Fill in the TODOs with actual game state setup and assertions.
"""
import pytest
from ptcg.core.card_registry import registry


def make_card():
    c = registry.get("PRE-106")
    if c is None:
        pytest.skip("PRE-106 not registered")
    return c()


class Test大地容器SpecRules:
    def test_text_rules_present(self):
        card = make_card()
        # Rule: 将自己的1张手牌丢于弃牌区（若无法丢弃则无法使用）
        # Rule: 选择自己牌库中最多2张基本能量
        # Rule: 在给对手看过之后加入手牌
        # Rule: 并重洗牌库
        assert card.text  # Card has effect text

class Test大地容器SpecScenarios:
    @pytest.mark.skip(reason="Auto-generated skeleton — needs manual setup")
    def test_正常_选择丢弃_选2张基本能量_加入手牌(self, snapshot_game):
        """正常：选择丢弃→选2张基本能量→加入手牌"""
        h = snapshot_game
        card = make_card()
        # Expected: discard_chosen = True
        # Expected: energies_to_hand = 2
        # Expected: deck_shuffled = True
        # TODO: h.set_hand(...), set_deck(...), execute action, assert

    @pytest.mark.skip(reason="Auto-generated skeleton — needs manual setup")
    def test_边界_手牌只有大地容器自身(self, snapshot_game):
        """边界：手牌只有大地容器自身"""
        h = snapshot_game
        card = make_card()
        # Expected: cannot_use = True
        # TODO: h.set_hand(...), set_deck(...), execute action, assert

    @pytest.mark.skip(reason="Auto-generated skeleton — needs manual setup")
    def test_边界_牌库无基本能量(self, snapshot_game):
        """边界：牌库无基本能量"""
        h = snapshot_game
        card = make_card()
        # Expected: discard_chosen = True
        # Expected: energies_to_hand = 0
        # Expected: deck_shuffled = True
        # TODO: h.set_hand(...), set_deck(...), execute action, assert

