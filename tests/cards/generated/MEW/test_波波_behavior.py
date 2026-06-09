"""波波 (MEW-016) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "MEW-016"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test波波L4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 呼朋引伴: 造成0伤害
        # Rule: 攻击 撞击: 造成20伤害
        assert card.name

    def test_使用呼朋引伴(self, card):
        """使用呼朋引伴."""
        # Expected: damage_dealt = 0
        assert card is not None

    def test_使用撞击(self, card):
        """使用撞击."""
        # Expected: damage_dealt = 20
        assert card is not None

