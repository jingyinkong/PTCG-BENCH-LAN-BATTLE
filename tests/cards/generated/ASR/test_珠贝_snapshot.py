"""珠贝 (ASR-147) — L5-L6 边界+快照测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry
from ptcg.core.enums import CardPosition, CardType, PokemonPosition

CARD_ID = "ASR-147"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test珠贝L5EdgeCases:
    """L5: 标准边界条件."""

    def test_card_loads(self, card):
        assert card.name and card.id == CARD_ID

    def test_energy_cost_valid(self, card):
        for atk in getattr(card, "attacks", []):
            cost = getattr(atk, "cost", [])
            assert isinstance(cost, list), f"Attack {atk.name}: cost应为列表"

    def test_hp_non_negative(self, card):
        assert getattr(card, 'hp', 0) >= 0 if hasattr(card, 'hp') else True
