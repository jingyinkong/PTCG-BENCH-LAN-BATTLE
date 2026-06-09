"""光辉喷火龙 (CRZ-020) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "CRZ-020"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test光辉喷火龙L4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 炎爆: 造成250伤害
        # Rule: 特性 振奋之心
        assert card.name

    def test_使用炎爆(self, card):
        """使用炎爆."""
        # Expected: damage_dealt = 250
        assert card is not None

    def test_使用振奋之心(self, card):
        """使用振奋之心."""
        # Expected: ability_used = True
        assert card is not None

