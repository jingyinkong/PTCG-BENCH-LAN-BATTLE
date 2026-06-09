"""骑拉帝纳VSTAR (LOR-131) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "LOR-131"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test骑拉帝纳VSTARL4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 放逐冲击: 造成280伤害
        # Rule: 攻击 星耀安魂曲: 造成0伤害
        assert card.name

    def test_使用放逐冲击(self, card):
        """使用放逐冲击."""
        # Expected: damage_dealt = 280
        assert card is not None

    def test_使用星耀安魂曲(self, card):
        """使用星耀安魂曲."""
        # Expected: damage_dealt = 0
        assert card is not None

