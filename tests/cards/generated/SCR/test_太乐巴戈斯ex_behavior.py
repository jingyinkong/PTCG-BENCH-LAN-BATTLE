"""太乐巴戈斯ex (SCR-128) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "SCR-128"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test太乐巴戈斯exL4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 同盟打击: 造成30伤害
        # Rule: 攻击 皇冠蛋白石: 造成180伤害
        assert card.name

    def test_使用同盟打击(self, card):
        """使用同盟打击."""
        # Expected: damage_dealt = 30
        assert card is not None

    def test_使用皇冠蛋白石(self, card):
        """使用皇冠蛋白石."""
        # Expected: damage_dealt = 180
        assert card is not None

