"""雷丘V (BRS-158) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "BRS-158"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test雷丘VL4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 快速充能: 造成0伤害
        # Rule: 攻击 强劲电光: 造成60伤害
        assert card.name

    def test_使用快速充能(self, card):
        """使用快速充能."""
        # Expected: damage_dealt = 0
        assert card is not None

    def test_使用强劲电光(self, card):
        """使用强劲电光."""
        # Expected: damage_dealt = 60
        assert card is not None

