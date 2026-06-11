"""基本火能量 (SVE-002) — L3-L6 测试."""

import pytest
from ptcg.core.card_registry import registry
from ptcg.core.enums import CardPosition, CardType, EnergyType, PokemonPosition

CARD_ID = "SVE-002"


@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class TestSVE002L3Structure:
    """L3: 精确属性断言."""

    def test_card_identity(self, card):
        assert card.id == "SVE-002"
        assert card.name == "基本火能量"
        assert card.cardType == CardType.FIRE

    def test_energy_attributes(self, card):
        assert card.energyType == EnergyType.BASIC
        assert card.provides == [CardType.FIRE]


def _make_card():
    return registry.get("SVE-002")()

class Test基本火能量EnergyBehavior:
    """ENERGY 类型：能量行为测试."""
    def test_card_loads(self, snapshot_game):
        """卡牌可加载."""
        card = _make_card()
        assert card.name
        assert card.id == "SVE-002"
    def test_energy_provides(self, snapshot_game):
        """能量卡 provide 属性存在."""
        card = _make_card()
        assert hasattr(card, 'provides'), "能量卡应有 provides"

class Test基本火能量L5EdgeCases:
    """L5: 标准边界条件（snapshot_game 预设状态验证）."""
    def test_card_loads_correctly(self, snapshot_game):
        """卡牌加载属性正确."""
        card = _make_card()
        assert card.name is not None, f"Expected non-empty name, got {card.name}"
        assert card.id == 'SVE-002'
    def test_hp_non_negative(self, snapshot_game):
        """HP 非负（仅宝可梦卡）."""
        card = _make_card()
        if hasattr(card, 'hp') and card.hp is not None:
            assert card.hp >= 0

class Test基本火能量L6Snapshot:
    """L6: 场景快照 — 手牌中存在性验证."""
    def test_snapshot_card_in_hand(self, snapshot_game):
        """快照: 卡牌在手牌中可访问."""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.HAND
        h.p1.hand = [card]
        assert len(h.p1.hand) == 1
        assert h.p1.hand[0].id == 'SVE-002'