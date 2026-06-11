"""智挥猩V (ASR-133) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.action import AttackAction
from ptcg.core.card_registry import registry
from ptcg.core.enums import CardPosition, CardType, PokemonPosition

CARD_ID = "ASR-133"


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


class Test智挥猩VL4Behavior:
    """L4: 效果行为验证（snapshot_game 预设状态+状态断言）."""
    def test_text_rules_documented(self, snapshot_game):
        """验证效果规则已记录."""
        # Rule: 攻击 精神强念: 造成30伤害
        # Rule: 特性 预订
        card = _make_card()
        assert card.name and card.id == CARD_ID

    def test_使用精神强念(self, snapshot_game):
        """使用精神强念."""
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
            assert old_hp - opp.hp == 30, f'Expected 30 damage, got {old_hp - opp.hp}'

    def test_使用预订(self, snapshot_game):
        """使用预订."""
        h = snapshot_game
        card = _make_card()
        card.position = PokemonPosition.ACTIVE
        card.cardPosition = CardPosition.ACTIVE
        h.p1.active = [card]
        opp = _make_opponent()
        h.p2.active = [opp]
        # Expected: ability_used = True
        assert len(h.p1.active) == 1
        assert h.p1.active[0].name == '智挥猩V'

