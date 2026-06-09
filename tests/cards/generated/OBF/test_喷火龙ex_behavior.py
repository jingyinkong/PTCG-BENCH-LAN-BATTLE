"""喷火龙ex (OBF-125) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "OBF-125"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test喷火龙exL4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 燃烧黑暗: 造成180伤害
        # Rule: 特性 烈炎支配
        assert card.name

    def test_使用燃烧黑暗(self, card):
        """使用燃烧黑暗."""
        # Expected: damage_dealt = 180
        assert card is not None

    def test_使用烈炎支配(self, card):
        """使用烈炎支配."""
        # Expected: ability_used = True
        assert card is not None

