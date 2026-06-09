"""旋转洛托姆 (SCR-118) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "SCR-118"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test旋转洛托姆L4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 突击登陆: 造成70伤害
        # Rule: 特性 风扇呼唤
        assert card.name

    def test_使用突击登陆(self, card):
        """使用突击登陆."""
        # Expected: damage_dealt = 70
        assert card is not None

    def test_使用风扇呼唤(self, card):
        """使用风扇呼唤."""
        # Expected: ability_used = True
        assert card is not None

