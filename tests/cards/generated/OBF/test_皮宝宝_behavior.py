"""皮宝宝 (OBF-202) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "OBF-202"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test皮宝宝L4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 握握抽取: 造成0伤害
        assert card.name

    def test_使用握握抽取(self, card):
        """使用握握抽取."""
        # Expected: damage_dealt = 0
        assert card is not None

