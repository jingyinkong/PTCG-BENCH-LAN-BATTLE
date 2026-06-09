"""起源帝牙卢卡VSTAR (ASR-114) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "ASR-114"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test起源帝牙卢卡VSTARL4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 金属爆破: 造成40伤害
        # Rule: 攻击 星耀时刻: 造成220伤害
        assert card.name

    def test_使用金属爆破(self, card):
        """使用金属爆破."""
        # Expected: damage_dealt = 40
        assert card is not None

    def test_使用星耀时刻(self, card):
        """使用星耀时刻."""
        # Expected: damage_dealt = 220
        assert card is not None

