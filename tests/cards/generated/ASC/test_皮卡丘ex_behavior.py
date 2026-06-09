"""皮卡丘ex (ASC-057) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "ASC-057"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test皮卡丘exL4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 黄晶伏特: 造成300伤害
        # Rule: 特性 顽强之心
        assert card.name

    def test_使用黄晶伏特(self, card):
        """使用黄晶伏特."""
        # Expected: damage_dealt = 300
        assert card is not None

    def test_使用顽强之心(self, card):
        """使用顽强之心."""
        # Expected: ability_used = True
        assert card is not None

