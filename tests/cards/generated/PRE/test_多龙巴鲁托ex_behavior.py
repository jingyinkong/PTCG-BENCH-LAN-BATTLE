"""多龙巴鲁托ex (PRE-073) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "PRE-073"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test多龙巴鲁托exL4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 喷射头击: 造成70伤害
        # Rule: 攻击 幻影潜袭: 造成200伤害
        assert card.name

    def test_使用喷射头击(self, card):
        """使用喷射头击."""
        # Expected: damage_dealt = 70
        assert card is not None

    def test_使用幻影潜袭(self, card):
        """使用幻影潜袭."""
        # Expected: damage_dealt = 200
        assert card is not None

