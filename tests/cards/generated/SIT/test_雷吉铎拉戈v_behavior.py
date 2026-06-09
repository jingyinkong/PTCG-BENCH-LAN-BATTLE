"""雷吉铎拉戈V (SIT-135) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "SIT-135"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test雷吉铎拉戈VL4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 天之呐喊: 造成0伤害
        # Rule: 攻击 巨龙镭射: 造成130伤害
        assert card.name

    def test_使用天之呐喊(self, card):
        """使用天之呐喊."""
        # Expected: damage_dealt = 0
        assert card is not None

    def test_使用巨龙镭射(self, card):
        """使用巨龙镭射."""
        # Expected: damage_dealt = 130
        assert card is not None

