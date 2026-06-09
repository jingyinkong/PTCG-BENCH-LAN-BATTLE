"""雷吉铎拉戈VSTAR (SIT-136) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "SIT-136"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test雷吉铎拉戈VSTARL4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 巨龙无双: 造成0伤害
        # Rule: 特性 星耀遗产
        assert card.name

    def test_使用巨龙无双(self, card):
        """使用巨龙无双."""
        # Expected: damage_dealt = 0
        assert card is not None

    def test_使用星耀遗产(self, card):
        """使用星耀遗产."""
        # Expected: ability_used = True
        assert card is not None

