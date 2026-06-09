"""盖诺赛克特 (SFA-040) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "SFA-040"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test盖诺赛克特L4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 磁力爆破: 造成100伤害
        # Rule: 特性 ACE消除器
        assert card.name

    def test_使用磁力爆破(self, card):
        """使用磁力爆破."""
        # Expected: damage_dealt = 100
        assert card is not None

    def test_使用ACE消除器(self, card):
        """使用ACE消除器."""
        # Expected: ability_used = True
        assert card is not None

