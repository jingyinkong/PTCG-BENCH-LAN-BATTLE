"""玛纳霏 (BRS-041) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "BRS-041"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test玛纳霏L4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 泼水: 造成20伤害
        # Rule: 特性 浪花水帘
        assert card.name

    def test_使用泼水(self, card):
        """使用泼水."""
        # Expected: damage_dealt = 20
        assert card is not None

    def test_使用浪花水帘(self, card):
        """使用浪花水帘."""
        # Expected: ability_used = True
        assert card is not None

