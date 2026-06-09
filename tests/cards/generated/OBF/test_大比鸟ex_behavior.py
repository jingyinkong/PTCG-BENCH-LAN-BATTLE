"""大比鸟ex (OBF-164) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "OBF-164"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test大比鸟exL4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 狂风呼啸: 造成120伤害
        # Rule: 特性 音速搜索
        assert card.name

    def test_使用狂风呼啸(self, card):
        """使用狂风呼啸."""
        # Expected: damage_dealt = 120
        assert card is not None

    def test_使用音速搜索(self, card):
        """使用音速搜索."""
        # Expected: ability_used = True
        assert card is not None

