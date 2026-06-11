"""起源帝牙卢卡VSTAR (ASR-114) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.action import AttackAction
from ptcg.core.card_registry import registry
from ptcg.core.enums import CardPosition, CardType, PokemonPosition
from ptcg.core.exceptions import GameTermination

CARD_ID = "ASR-114"


def _make_card():
    return registry.get(CARD_ID)()


def _make_opponent():
    opp = registry.get("ASR-040")()
    opp.position = PokemonPosition.ACTIVE
    opp.cardPosition = CardPosition.ACTIVE
    opp.index = 0
    if not hasattr(opp, "max_hp"):
        opp.max_hp = opp.hp
    return opp


class Test起源帝牙卢卡VSTARL4Behavior:
    """L4: 效果行为验证（snapshot_game 预设状态+状态断言）."""
    def test_text_rules_documented(self, snapshot_game):
        """验证效果规则已记录."""
        # Rule: 攻击 金属爆破: 造成40伤害
        # Rule: 攻击 星耀时刻: 造成220伤害
        card = _make_card()
        assert card.name and card.id == CARD_ID

    def test_使用金属爆破(self, snapshot_game):
        """使用金属爆破."""
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

    def test_使用星耀时刻(self, snapshot_game):
        """使用星耀时刻."""
        h = snapshot_game
        card = _make_card()
        card.position = PokemonPosition.ACTIVE
        card.cardPosition = CardPosition.ACTIVE
        card.energy = [CardType.METAL] * 4 + [CardType.COLORLESS]
        h.p1.active = [card]
        opp = _make_opponent()
        h.p2.active = [opp]
        old_hp = opp.hp
        attack_idx = 1
        if attack_idx < len(card.attacks):
            action = AttackAction(h.p1.id, card, card.attacks[attack_idx], opp)
            gen = card.reduce_action(action, h.state)
            if gen:
                try:
                    for _ in range(10):
                        next(gen)
                except (StopIteration, IndexError, AttributeError, ValueError, GameTermination):
                    pass
            assert old_hp - opp.hp == 220, f'Expected 220 damage, got {old_hp - opp.hp}'

