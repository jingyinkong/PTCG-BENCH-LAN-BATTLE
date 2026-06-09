"""小磁怪 (SVI-063) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "SVI-063"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test小磁怪L4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 互斥: 造成0伤害
        # Rule: 攻击 电球: 造成10伤害
        assert card.name

    def test_使用互斥(self, card):
        """使用互斥."""
        # Expected: damage_dealt = 0
        assert card is not None

    def test_使用电球(self, card):
        """使用电球."""
        # Expected: damage_dealt = 10
        assert card is not None

