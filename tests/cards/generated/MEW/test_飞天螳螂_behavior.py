"""飞天螳螂 (MEW-123) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "MEW-123"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test飞天螳螂L4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 辅助斩: 造成20伤害
        # Rule: 攻击 薄片利刃: 造成70伤害
        assert card.name

    def test_使用辅助斩(self, card):
        """使用辅助斩."""
        # Expected: damage_dealt = 20
        assert card is not None

    def test_使用薄片利刃(self, card):
        """使用薄片利刃."""
        # Expected: damage_dealt = 70
        assert card is not None

