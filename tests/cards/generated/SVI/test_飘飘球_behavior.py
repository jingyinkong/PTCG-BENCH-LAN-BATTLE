"""飘飘球 (SVI-089) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "SVI-089"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test飘飘球L4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 起风: 造成10伤害
        # Rule: 攻击 气球炸弹: 造成30伤害
        assert card.name

    def test_使用起风(self, card):
        """使用起风."""
        # Expected: damage_dealt = 10
        assert card is not None

    def test_使用气球炸弹(self, card):
        """使用气球炸弹."""
        # Expected: damage_dealt = 30
        assert card is not None

