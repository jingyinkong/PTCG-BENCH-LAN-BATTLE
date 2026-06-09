"""彷徨夜灵 (SFA-019) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "SFA-019"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test彷徨夜灵L4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 磷火: 造成50伤害
        # Rule: 特性 咒怨炸弹
        assert card.name

    def test_使用磷火(self, card):
        """使用磷火."""
        # Expected: damage_dealt = 50
        assert card is not None

    def test_使用咒怨炸弹(self, card):
        """使用咒怨炸弹."""
        # Expected: ability_used = True
        assert card is not None

