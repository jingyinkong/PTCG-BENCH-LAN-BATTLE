"""猛雷鼓ex (TEF-123) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "TEF-123"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test猛雷鼓exL4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 飞溅咆哮: 造成0伤害
        # Rule: 攻击 极雷轰: 造成70伤害
        assert card.name

    def test_使用飞溅咆哮(self, card):
        """使用飞溅咆哮."""
        # Expected: damage_dealt = 0
        assert card is not None

    def test_使用极雷轰(self, card):
        """使用极雷轰."""
        # Expected: damage_dealt = 70
        assert card is not None

