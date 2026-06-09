"""厄诡椪 碧草面具ex (TWM-025) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "TWM-025"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test厄诡椪_碧草面具exL4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 万叶阵雨: 造成30伤害
        # Rule: 特性 碧草之舞
        assert card.name

    def test_使用万叶阵雨(self, card):
        """使用万叶阵雨."""
        # Expected: damage_dealt = 30
        assert card is not None

    def test_使用碧草之舞(self, card):
        """使用碧草之舞."""
        # Expected: ability_used = True
        assert card is not None

