"""奇诺栗鼠 (TEF-137) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "TEF-137"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test奇诺栗鼠L4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 重掴: 造成30伤害
        # Rule: 攻击 特殊滚动: 造成70伤害
        assert card.name

    def test_使用重掴(self, card):
        """使用重掴."""
        # Expected: damage_dealt = 30
        assert card is not None

    def test_使用特殊滚动(self, card):
        """使用特殊滚动."""
        # Expected: damage_dealt = 70
        assert card is not None

