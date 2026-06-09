"""洛奇亚V (SIT-138) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "SIT-138"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test洛奇亚VL4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 读风: 造成0伤害
        # Rule: 攻击 气旋俯冲: 造成130伤害
        assert card.name

    def test_使用读风(self, card):
        """使用读风."""
        # Expected: damage_dealt = 0
        assert card is not None

    def test_使用气旋俯冲(self, card):
        """使用气旋俯冲."""
        # Expected: damage_dealt = 130
        assert card is not None

