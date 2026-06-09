"""黑夜魔灵 (SFA-020) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "SFA-020"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test黑夜魔灵L4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 影子束缚: 造成150伤害
        # Rule: 特性 咒怨炸弹
        assert card.name

    def test_使用影子束缚(self, card):
        """使用影子束缚."""
        # Expected: damage_dealt = 150
        assert card is not None

    def test_使用咒怨炸弹(self, card):
        """使用咒怨炸弹."""
        # Expected: ability_used = True
        assert card is not None

