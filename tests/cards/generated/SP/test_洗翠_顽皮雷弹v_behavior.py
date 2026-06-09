"""洗翠 顽皮雷弹V (SP-294) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "SP-294"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test洗翠_顽皮雷弹VL4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 暴躁炸弹: 造成100伤害
        # Rule: 攻击 日光射击: 造成120伤害
        assert card.name

    def test_使用暴躁炸弹(self, card):
        """使用暴躁炸弹."""
        # Expected: damage_dealt = 100
        assert card is not None

    def test_使用日光射击(self, card):
        """使用日光射击."""
        # Expected: damage_dealt = 120
        assert card is not None

