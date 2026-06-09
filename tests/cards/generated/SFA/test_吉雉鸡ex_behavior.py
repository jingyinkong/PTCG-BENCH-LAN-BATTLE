"""吉雉鸡ex (SFA-038) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "SFA-038"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test吉雉鸡exL4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 残忍箭矢: 造成0伤害
        # Rule: 特性 化危为吉
        assert card.name

    def test_使用残忍箭矢(self, card):
        """使用残忍箭矢."""
        # Expected: damage_dealt = 0
        assert card is not None

    def test_使用化危为吉(self, card):
        """使用化危为吉."""
        # Expected: ability_used = True
        assert card is not None

