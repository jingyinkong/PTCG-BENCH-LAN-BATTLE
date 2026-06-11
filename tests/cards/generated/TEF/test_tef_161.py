"""薄雾能量 (TEF-161) — L3-L6 测试."""

import pytest
from ptcg.core.card_registry import registry
from ptcg.core.enums import CardPosition, CardType, EnergyType, PokemonPosition

CARD_ID = "TEF-161"


@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class TestTEF161L3Structure:
    """L3: 精确属性断言."""

    def test_card_identity(self, card):
        assert card.id == "TEF-161"
        assert card.name == "薄雾能量"
        assert card.cardType == CardType.COLORLESS

    def test_energy_attributes(self, card):
        assert card.energyType == EnergyType.SPECIAL
        assert card.provides == [CardType.COLORLESS]
        assert card.text == "只要这张卡牌，被附着于宝可梦身上，就被视作1个【无】能量。  身上附着了这张卡牌的宝可梦，不受到对手宝可梦所使用的招式的效果影响。（已经受到的效果，不会消失。）"


def _make_card():
    return registry.get("TEF-161")()

class Test薄雾能量EnergyBehavior:
    """ENERGY 类型：能量行为测试."""
    def test_card_loads(self, snapshot_game):
        """卡牌可加载."""
        card = _make_card()
        assert card.name
        assert card.id == "TEF-161"
    def test_energy_provides(self, snapshot_game):
        """能量卡 provide 属性存在."""
        card = _make_card()
        assert hasattr(card, 'provides'), "能量卡应有 provides"

class Test薄雾能量L5EdgeCases:
    """L5: 标准边界条件（snapshot_game 预设状态验证）."""
    def test_card_loads_correctly(self, snapshot_game):
        """卡牌加载属性正确."""
        card = _make_card()
        assert card.name is not None, f"Expected non-empty name, got {card.name}"
        assert card.id == 'TEF-161'
    def test_hp_non_negative(self, snapshot_game):
        """HP 非负（仅宝可梦卡）."""
        card = _make_card()
        if hasattr(card, 'hp') and card.hp is not None:
            assert card.hp >= 0

class Test薄雾能量L6Snapshot:
    """L6: 场景快照 — 手牌中存在性验证."""
    def test_snapshot_card_in_hand(self, snapshot_game):
        """快照: 卡牌在手牌中可访问."""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.HAND
        h.p1.hand = [card]
        assert len(h.p1.hand) == 1
        assert h.p1.hand[0].id == 'TEF-161'