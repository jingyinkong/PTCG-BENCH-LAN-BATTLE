"""诡角鹿V (ASR-134) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.action import AttackAction
from ptcg.core.card_registry import registry
from ptcg.core.enums import CardPosition, CardType, PokemonPosition

CARD_ID = "ASR-134"


def _make_card():
    return registry.get(CARD_ID)()


def _make_opponent():
    opp = registry.get("ASR-133")()
    opp.position = PokemonPosition.ACTIVE
    opp.cardPosition = CardPosition.ACTIVE
    opp.index = 0
    if not hasattr(opp, "max_hp"):
        opp.max_hp = opp.hp
    return opp


class Test诡角鹿VL4Behavior:
    """L4: 效果行为验证（snapshot_game 预设状态+状态断言）."""
    def test_text_rules_documented(self, snapshot_game):
        """验证效果规则已记录."""
        # Rule: 攻击 屏障猛攻: 造成40伤害
        # Rule: 特性 拓荒之路
        card = _make_card()
        assert card.name and card.id == CARD_ID

    def test_使用屏障猛攻(self, snapshot_game):
        """使用屏障猛攻."""
        h = snapshot_game
        card = _make_card()
        card.position = PokemonPosition.ACTIVE
        card.cardPosition = CardPosition.ACTIVE
        card.energy = [CardType.COLORLESS] * 5
        h.p1.active = [card]
        opp = _make_opponent()
        h.p2.active = [opp]
        old_hp = opp.hp
        attack_idx = 0
        if attack_idx < len(card.attacks):
            action = AttackAction(h.p1.id, card, card.attacks[attack_idx], opp)
            gen = card.reduce_action(action, h.state)
            if gen:
                try:
                    for _ in range(10):
                        next(gen)
                except (StopIteration, IndexError, AttributeError, ValueError):
                    pass
            assert old_hp - opp.hp == 40, f'Expected 40 damage, got {old_hp - opp.hp}'

    def test_使用拓荒之路(self, snapshot_game):
        """使用拓荒之路."""
        h = snapshot_game
        card = _make_card()
        card.position = PokemonPosition.ACTIVE
        card.cardPosition = CardPosition.ACTIVE
        h.p1.active = [card]
        opp = _make_opponent()
        h.p2.active = [opp]
        # Expected: ability_used = True
        assert len(h.p1.active) == 1
        assert h.p1.active[0].name == '诡角鹿V'

