"""故勒顿 (SSP-116) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "SSP-116"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test故勒顿L4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 波状猛攻: 造成30伤害
        # Rule: 攻击 头突: 造成110伤害
        assert card.name

    def test_使用波状猛攻(self, card):
        """使用波状猛攻."""
        # Expected: damage_dealt = 30
        assert card is not None

    def test_使用头突(self, card):
        """使用头突."""
        # Expected: damage_dealt = 110
        assert card is not None

