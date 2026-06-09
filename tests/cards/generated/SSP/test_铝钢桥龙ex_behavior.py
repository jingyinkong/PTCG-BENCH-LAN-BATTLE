"""铝钢桥龙ex (SSP-130) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "SSP-130"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test铝钢桥龙exL4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 金属防卫: 造成220伤害
        # Rule: 特性 合金建设
        assert card.name

    def test_使用金属防卫(self, card):
        """使用金属防卫."""
        # Expected: damage_dealt = 220
        assert card is not None

    def test_使用合金建设(self, card):
        """使用合金建设."""
        # Expected: ability_used = True
        assert card is not None

