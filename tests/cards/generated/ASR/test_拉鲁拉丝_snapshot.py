"""拉鲁拉丝 (ASR-060) — L5-L6 边界+快照测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry
from ptcg.core.enums import CardPosition, CardType, PokemonPosition

CARD_ID = "ASR-060"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test拉鲁拉丝L5EdgeCases:
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


class Test拉鲁拉丝L6Snapshot:
    """L6: 场景快照（snapshot_game 预设全游戏状态 → 执行动作 → 状态断言）."""
    def test_snapshot_使用瞬移破坏(self, snapshot_game):
        """使用瞬移破坏."""
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
            assert old_hp - opp.hp == 10, f'Expected 10 damage, got {old_hp - opp.hp}'

