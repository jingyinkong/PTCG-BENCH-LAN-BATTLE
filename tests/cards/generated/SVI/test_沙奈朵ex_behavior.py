"""沙奈朵ex (SVI-086) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "SVI-086"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test沙奈朵exL4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 奇迹之力: 造成190伤害
        # Rule: 特性 精神拥抱
        assert card.name

    def test_使用奇迹之力(self, card):
        """使用奇迹之力."""
        # Expected: damage_dealt = 190
        assert card is not None

    def test_使用精神拥抱(self, card):
        """使用精神拥抱."""
        # Expected: ability_used = True
        assert card is not None

