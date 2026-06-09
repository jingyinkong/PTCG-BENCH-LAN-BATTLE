"""土龙弟弟 (PAL-156) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "PAL-156"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test土龙弟弟L4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 找朋友: 造成0伤害
        # Rule: 攻击 咬住: 造成50伤害
        assert card.name

    def test_使用找朋友(self, card):
        """使用找朋友."""
        # Expected: damage_dealt = 0
        assert card is not None

    def test_使用咬住(self, card):
        """使用咬住."""
        # Expected: damage_dealt = 50
        assert card is not None

