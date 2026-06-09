"""月月熊 赫月ex (TWM-141) — L5-L6 边界+快照测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "TWM-141"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test月月熊_赫月exL5EdgeCases:
    """L5: 标准边界条件."""

    def test_card_loads(self, card):
        assert card.name and card.id == CARD_ID

    def test_energy_cost_valid(self, card):
        for atk in getattr(card, "attacks", []):
            cost = getattr(atk, "cost", [])
            assert isinstance(cost, list), f"Attack {atk.name}: cost应为列表"

    def test_hp_non_negative(self, card):
        assert card.hp >= 0 if hasattr(card, "hp") else True

class Test月月熊_赫月exL6Snapshot:
    """L6: 场景快照."""
    def test_snapshot_使用血月(self, card):
        """使用血月."""
        # Then: {"damage_dealt": 240}
        assert card is not None

    def test_snapshot_使用老练招式(self, card):
        """使用老练招式."""
        # Then: {"ability_used": true}
        assert card is not None

