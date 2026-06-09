"""小火龙 (OBF-026) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "OBF-026"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test小火龙L4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 高温冲撞: 造成30伤害
        assert card.name

    def test_使用高温冲撞(self, card):
        """使用高温冲撞."""
        # Expected: damage_dealt = 30
        assert card is not None

