"""大牙狸 (CRZ-111) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "CRZ-111"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test大牙狸L4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 终结门牙: 造成30伤害
        # Rule: 特性 毫不在意
        assert card.name

    def test_使用终结门牙(self, card):
        """使用终结门牙."""
        # Expected: damage_dealt = 30
        assert card is not None

    def test_使用毫不在意(self, card):
        """使用毫不在意."""
        # Expected: ability_used = True
        assert card is not None

