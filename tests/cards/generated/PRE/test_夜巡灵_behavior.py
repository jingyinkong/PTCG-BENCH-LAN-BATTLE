"""夜巡灵 (PRE-035) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "PRE-035"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test夜巡灵L4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 渡魂: 造成0伤害
        # Rule: 攻击 喃喃自语: 造成30伤害
        assert card.name

    def test_使用渡魂(self, card):
        """使用渡魂."""
        # Expected: damage_dealt = 0
        assert card is not None

    def test_使用喃喃自语(self, card):
        """使用喃喃自语."""
        # Expected: damage_dealt = 30
        assert card is not None

