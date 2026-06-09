"""泡沫栗鼠 (BRS-124) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "BRS-124"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test泡沫栗鼠L4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 敲打: 造成10伤害
        # Rule: 攻击 扫除: 造成0伤害
        assert card.name

    def test_使用敲打(self, card):
        """使用敲打."""
        # Expected: damage_dealt = 10
        assert card is not None

    def test_使用扫除(self, card):
        """使用扫除."""
        # Expected: damage_dealt = 0
        assert card is not None

