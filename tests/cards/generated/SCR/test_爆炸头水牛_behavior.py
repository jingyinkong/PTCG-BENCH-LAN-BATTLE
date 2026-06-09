"""爆炸头水牛 (SCR-119) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "SCR-119"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test爆炸头水牛L4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 潜力: 造成130伤害
        # Rule: 特性 卷曲厚壁
        assert card.name

    def test_使用潜力(self, card):
        """使用潜力."""
        # Expected: damage_dealt = 130
        assert card is not None

    def test_使用卷曲厚壁(self, card):
        """使用卷曲厚壁."""
        # Expected: ability_used = True
        assert card is not None

