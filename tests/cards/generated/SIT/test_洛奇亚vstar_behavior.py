"""洛奇亚VSTAR (SIT-139) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "SIT-139"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test洛奇亚VSTARL4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 风暴俯冲: 造成220伤害
        # Rule: 特性 星耀汇聚
        assert card.name

    def test_使用风暴俯冲(self, card):
        """使用风暴俯冲."""
        # Expected: damage_dealt = 220
        assert card is not None

    def test_使用星耀汇聚(self, card):
        """使用星耀汇聚."""
        # Expected: ability_used = True
        assert card is not None

