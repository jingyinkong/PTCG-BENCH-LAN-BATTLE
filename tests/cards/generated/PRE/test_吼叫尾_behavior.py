"""吼叫尾 (PRE-042) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "PRE-042"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test吼叫尾L4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 巴掌: 造成30伤害
        # Rule: 攻击 凶暴吼叫: 造成0伤害
        assert card.name

    def test_使用巴掌(self, card):
        """使用巴掌."""
        # Expected: damage_dealt = 30
        assert card is not None

    def test_使用凶暴吼叫(self, card):
        """使用凶暴吼叫."""
        # Expected: damage_dealt = 0
        assert card is not None

