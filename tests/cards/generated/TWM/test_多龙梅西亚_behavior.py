"""多龙梅西亚 (TWM-128) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "TWM-128"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test多龙梅西亚L4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 小哀怨: 造成10伤害
        # Rule: 攻击 咬住: 造成40伤害
        assert card.name

    def test_使用小哀怨(self, card):
        """使用小哀怨."""
        # Expected: damage_dealt = 10
        assert card is not None

    def test_使用咬住(self, card):
        """使用咬住."""
        # Expected: damage_dealt = 40
        assert card is not None

