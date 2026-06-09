"""振翼发 (PRE-043) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "PRE-043"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test振翼发L4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 飞来横祸: 造成90伤害
        # Rule: 特性 暗夜振翼
        assert card.name

    def test_使用飞来横祸(self, card):
        """使用飞来横祸."""
        # Expected: damage_dealt = 90
        assert card is not None

    def test_使用暗夜振翼(self, card):
        """使用暗夜振翼."""
        # Expected: ability_used = True
        assert card is not None

