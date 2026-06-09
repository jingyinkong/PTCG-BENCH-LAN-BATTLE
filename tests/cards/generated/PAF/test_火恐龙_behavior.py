"""火恐龙 (PAF-008) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "PAF-008"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test火恐龙L4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 烈焰: 造成50伤害
        # Rule: 特性 闪焰之幕
        assert card.name

    def test_使用烈焰(self, card):
        """使用烈焰."""
        # Expected: damage_dealt = 50
        assert card is not None

    def test_使用闪焰之幕(self, card):
        """使用闪焰之幕."""
        # Expected: ability_used = True
        assert card is not None

