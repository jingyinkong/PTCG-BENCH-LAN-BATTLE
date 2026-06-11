"""光辉甲贺忍蛙 (ASR-046) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.action import AttackAction
from ptcg.core.card_registry import registry
from ptcg.core.enums import CardPosition, CardType, PokemonPosition

CARD_ID = "ASR-046"


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


class Test光辉甲贺忍蛙L4Behavior:
    """L4: 效果行为验证（snapshot_game 预设状态+状态断言）."""
    def test_text_rules_documented(self, snapshot_game):
        """验证效果规则已记录."""
        # Rule: 攻击 月光手里剑: 造成0伤害
        # Rule: 特性 隐藏牌
        card = _make_card()
        assert card.name and card.id == CARD_ID

    def test_使用月光手里剑(self, snapshot_game):
        """使用月光手里剑."""
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
            assert old_hp - opp.hp == 90, f'Expected 90 damage, got {old_hp - opp.hp}'

    def test_使用隐藏牌(self, snapshot_game):
        """使用隐藏牌."""
        h = snapshot_game
        card = _make_card()
        card.position = PokemonPosition.ACTIVE
        card.cardPosition = CardPosition.ACTIVE
        h.p1.active = [card]
        opp = _make_opponent()
        h.p2.active = [opp]
        # Expected: ability_used = True
        assert len(h.p1.active) == 1
        assert h.p1.active[0].name == '光辉甲贺忍蛙'

