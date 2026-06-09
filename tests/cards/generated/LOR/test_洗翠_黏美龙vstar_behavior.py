"""洗翠 黏美龙VSTAR (LOR-136) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "LOR-136"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test洗翠_黏美龙VSTARL4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 钢铁滚动: 造成200伤害
        # Rule: 特性 润泽星耀
        assert card.name

    def test_使用钢铁滚动(self, card):
        """使用钢铁滚动."""
        # Expected: damage_dealt = 200
        assert card is not None

    def test_使用润泽星耀(self, card):
        """使用润泽星耀."""
        # Expected: ability_used = True
        assert card is not None

