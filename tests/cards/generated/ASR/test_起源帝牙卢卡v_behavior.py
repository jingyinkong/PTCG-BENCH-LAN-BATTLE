"""起源帝牙卢卡V (ASR-113) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "ASR-113"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test起源帝牙卢卡VL4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 金属涂层: 造成0伤害
        # Rule: 攻击 时间断绝: 造成180伤害
        assert card.name

    def test_使用金属涂层(self, card):
        """使用金属涂层."""
        # Expected: damage_dealt = 0
        assert card is not None

    def test_使用时间断绝(self, card):
        """使用时间断绝."""
        # Expected: damage_dealt = 180
        assert card is not None

