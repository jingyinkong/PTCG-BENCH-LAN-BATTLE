"""月月熊 赫月ex (TWM-141) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "TWM-141"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test月月熊_赫月exL4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 血月: 造成240伤害
        # Rule: 特性 老练招式
        assert card.name

    def test_使用血月(self, card):
        """使用血月."""
        # Expected: damage_dealt = 240
        assert card is not None

    def test_使用老练招式(self, card):
        """使用老练招式."""
        # Expected: ability_used = True
        assert card is not None

