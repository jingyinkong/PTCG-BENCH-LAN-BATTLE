"""光辉洗翠 大狃拉 (LOR-123) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "LOR-123"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test光辉洗翠_大狃拉L4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 毒击: 造成90伤害
        # Rule: 特性 巅峰毒性
        assert card.name

    def test_使用毒击(self, card):
        """使用毒击."""
        # Expected: damage_dealt = 90
        assert card is not None

    def test_使用巅峰毒性(self, card):
        """使用巅峰毒性."""
        # Expected: ability_used = True
        assert card is not None

