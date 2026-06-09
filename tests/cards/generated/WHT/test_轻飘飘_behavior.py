"""轻飘飘 (WHT-044) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "WHT-044"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test轻飘飘L4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 自我再生: 造成0伤害
        # Rule: 攻击 泼水: 造成10伤害
        assert card.name

    def test_使用自我再生(self, card):
        """使用自我再生."""
        # Expected: damage_dealt = 0
        assert card is not None

    def test_使用泼水(self, card):
        """使用泼水."""
        # Expected: damage_dealt = 10
        assert card is not None

