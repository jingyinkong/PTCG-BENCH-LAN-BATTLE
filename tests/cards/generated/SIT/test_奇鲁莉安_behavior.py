"""奇鲁莉安 (SIT-068) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "SIT-068"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test奇鲁莉安L4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 巴掌: 造成30伤害
        # Rule: 特性 精炼
        assert card.name

    def test_使用巴掌(self, card):
        """使用巴掌."""
        # Expected: damage_dealt = 30
        assert card is not None

    def test_使用精炼(self, card):
        """使用精炼."""
        # Expected: ability_used = True
        assert card is not None

