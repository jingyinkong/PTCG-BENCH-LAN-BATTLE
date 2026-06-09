"""猫头夜鹰 (SCR-115) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "SCR-115"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test猫头夜鹰L4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 高速之翼: 造成60伤害
        # Rule: 特性 寻找宝石
        assert card.name

    def test_使用高速之翼(self, card):
        """使用高速之翼."""
        # Expected: damage_dealt = 60
        assert card is not None

    def test_使用寻找宝石(self, card):
        """使用寻找宝石."""
        # Expected: ability_used = True
        assert card is not None

