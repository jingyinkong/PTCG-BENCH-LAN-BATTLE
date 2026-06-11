"""起源帝牙卢卡VSTAR (ASR-114) — L5-L6 边界+快照测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry
from ptcg.core.enums import CardPosition, CardType, PokemonPosition

CARD_ID = "ASR-114"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test起源帝牙卢卡VSTARL5EdgeCases:
    """L5: 标准边界条件."""

    def test_card_loads(self, card):
        assert card.name and card.id == CARD_ID

    def test_energy_cost_valid(self, card):
        for atk in getattr(card, "attacks", []):
            cost = getattr(atk, "cost", [])
            assert isinstance(cost, list), f"Attack {atk.name}: cost应为列表"

    def test_hp_non_negative(self, card):
        assert getattr(card, 'hp', 0) >= 0 if hasattr(card, 'hp') else True

from ptcg.core.action import AttackAction
from ptcg.core.exceptions import GameTermination


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


class Test起源帝牙卢卡VSTARL6Snapshot:
    """L6: 场景快照（snapshot_game 预设全游戏状态 → 执行动作 → 状态断言）."""
    def test_snapshot_使用金属爆破(self, snapshot_game):
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

    def test_snapshot_使用星耀时刻(self, snapshot_game):
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

