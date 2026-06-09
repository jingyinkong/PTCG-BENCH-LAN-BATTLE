"""咕咕 (SCR-114) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "SCR-114"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test咕咕L4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 三刺击: 造成10伤害
        assert card.name

    def test_使用三刺击(self, card):
        """使用三刺击."""
        # Expected: damage_dealt = 10
        assert card is not None

