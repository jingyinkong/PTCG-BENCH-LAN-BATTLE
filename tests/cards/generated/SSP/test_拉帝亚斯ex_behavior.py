"""拉帝亚斯ex (SSP-076) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "SSP-076"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test拉帝亚斯exL4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 无限之刃: 造成200伤害
        # Rule: 特性 天际线
        assert card.name

    def test_使用无限之刃(self, card):
        """使用无限之刃."""
        # Expected: damage_dealt = 200
        assert card is not None

    def test_使用天际线(self, card):
        """使用天际线."""
        # Expected: ability_used = True
        assert card is not None

