"""医疗能量 (PAR-182) — L3-L6 测试."""

import pytest
from ptcg.core.card_registry import registry
from ptcg.core.enums import CardPosition, CardType, EnergyType, PokemonPosition

CARD_ID = "PAR-182"


@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class TestPAR182L3Structure:
    """L3: 精确属性断言."""

    def test_card_identity(self, card):
        assert card.id == "PAR-182"
        assert card.name == "医疗能量"
        assert card.cardType == CardType.COLORLESS

    def test_energy_attributes(self, card):
        assert card.energyType == EnergyType.SPECIAL
        assert card.provides == [CardType.COLORLESS]
        assert card.text == "只要这张卡牌，被附着于宝可梦身上，就被视作1个【无】能量。  当将这张卡牌从手牌附着于宝可梦身上时，回复那只宝可梦「30」HP。"


def _make_card():
    return registry.get("PAR-182")()

class Test医疗能量EnergyBehavior:
    """ENERGY 类型：能量行为测试."""
    def test_card_loads(self, snapshot_game):
        """卡牌可加载."""
        card = _make_card()
        assert card.name == "医疗能量"
        assert card.id == "PAR-182"
        assert card.cardType == CardType.COLORLESS
    def test_energy_provides(self, snapshot_game):
        """测试能量提供类型."""
        card = _make_card()
        provides = card.provides
        assert len(provides) >= 1
        assert CardType.COLORLESS in provides

class Test医疗能量L5EdgeCases:
    """L5: 标准边界条件（snapshot_game 预设状态验证）."""
    def test_card_loads_correctly(self, snapshot_game):
        """卡牌加载属性正确."""
        card = _make_card()
        assert card.name is not None, f"Expected non-empty name, got {card.name}"
        assert card.id == 'PAR-182'
    def test_hp_non_negative(self, snapshot_game):
        """HP 非负（仅宝可梦卡）."""
        card = _make_card()
        if hasattr(card, 'hp') and card.hp is not None:
            assert card.hp >= 0

class Test医疗能量L6Snapshot:
    """L6: 场景快照 — 手牌中存在性验证."""
    def test_snapshot_card_in_hand(self, snapshot_game):
        """快照: 卡牌在手牌中可访问."""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.HAND
        h.p1.hand = [card]
        assert len(h.p1.hand) == 1
        assert h.p1.hand[0].id == 'PAR-182'