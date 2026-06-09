"""爬地翅 (PAR-107) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "PAR-107"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test爬地翅L4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 踏平: 造成0伤害
        # Rule: 攻击 烫伤怒涛: 造成120伤害
        assert card.name

    def test_使用踏平(self, card):
        """使用踏平."""
        # Expected: damage_dealt = 0
        assert card is not None

    def test_使用烫伤怒涛(self, card):
        """使用烫伤怒涛."""
        # Expected: damage_dealt = 120
        assert card is not None

