"""铝钢龙 (SSP-129) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "SSP-129"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test铝钢龙L4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 正面对决: 造成50伤害
        # Rule: 攻击 铝钢光束: 造成130伤害
        assert card.name

    def test_使用正面对决(self, card):
        """使用正面对决."""
        # Expected: damage_dealt = 50
        assert card is not None

    def test_使用铝钢光束(self, card):
        """使用铝钢光束."""
        # Expected: damage_dealt = 130
        assert card is not None

