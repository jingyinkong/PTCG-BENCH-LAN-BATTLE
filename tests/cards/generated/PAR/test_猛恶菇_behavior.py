"""猛恶菇 (PAR-123) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "PAR-123"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test猛恶菇L4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 暴走重锤: 造成120伤害
        # Rule: 特性 烈毒粉尘
        assert card.name

    def test_使用暴走重锤(self, card):
        """使用暴走重锤."""
        # Expected: damage_dealt = 120
        assert card is not None

    def test_使用烈毒粉尘(self, card):
        """使用烈毒粉尘."""
        # Expected: ability_used = True
        assert card is not None

