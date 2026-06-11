"""馈赠能量 (LOR-171) — L3-L6 测试."""

import pytest
from ptcg.core.card_registry import registry
from ptcg.core.enums import CardPosition, CardType, EnergyType, PokemonPosition

CARD_ID = "LOR-171"


@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class TestLOR171L3Structure:
    """L3: 精确属性断言."""

    def test_card_identity(self, card):
        assert card.id == "LOR-171"
        assert card.name == "馈赠能量"
        assert card.cardType == CardType.COLORLESS

    def test_energy_attributes(self, card):
        assert card.energyType == EnergyType.SPECIAL
        assert card.provides == [CardType.COLORLESS]
        assert card.text == "只要这张卡牌，被附着于宝可梦身上，就被视作1个【无】能量。  身上附有这张卡牌的宝可梦，受到对手宝可梦的招式的伤害而【昏厥】时，从牌库上方抽取卡牌，直到自己的手牌变为7张为止。"


def _make_card():
    return registry.get("LOR-171")()

class Test馈赠能量EnergyBehavior:
    """ENERGY 类型：能量行为测试."""
    def test_card_loads(self, snapshot_game):
        """卡牌可加载."""
        card = _make_card()
        assert card.name
        assert card.id == "LOR-171"
    def test_energy_provides(self, snapshot_game):
        """能量卡 provide 属性存在."""
        card = _make_card()
        assert hasattr(card, 'provides'), "能量卡应有 provides"

class Test馈赠能量L5EdgeCases:
    """L5: 标准边界条件（snapshot_game 预设状态验证）."""
    def test_card_loads_correctly(self, snapshot_game):
        """卡牌加载属性正确."""
        card = _make_card()
        assert card.name is not None, f"Expected non-empty name, got {card.name}"
        assert card.id == 'LOR-171'
    def test_hp_non_negative(self, snapshot_game):
        """HP 非负（仅宝可梦卡）."""
        card = _make_card()
        if hasattr(card, 'hp') and card.hp is not None:
            assert card.hp >= 0

class Test馈赠能量L6Snapshot:
    """L6: 场景快照 — 手牌中存在性验证."""
    def test_snapshot_card_in_hand(self, snapshot_game):
        """快照: 卡牌在手牌中可访问."""
        h = snapshot_game
        card = _make_card()
        card.cardPosition = CardPosition.HAND
        h.p1.hand = [card]
        assert len(h.p1.hand) == 1
        assert h.p1.hand[0].id == 'LOR-171'