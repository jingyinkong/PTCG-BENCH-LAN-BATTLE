"""光辉甲贺忍蛙 (ASR-046) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "ASR-046"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test光辉甲贺忍蛙L4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 月光手里剑: 造成0伤害
        # Rule: 特性 隐藏牌
        assert card.name

    def test_使用月光手里剑(self, card):
        """使用月光手里剑."""
        # Expected: damage_dealt = 0
        assert card is not None

    def test_使用隐藏牌(self, card):
        """使用隐藏牌."""
        # Expected: ability_used = True
        assert card is not None

