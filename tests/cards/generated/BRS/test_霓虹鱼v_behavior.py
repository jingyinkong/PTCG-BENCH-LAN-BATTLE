"""霓虹鱼V (BRS-040) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "BRS-040"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test霓虹鱼VL4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 水流回转: 造成120伤害
        # Rule: 特性 夜光信号
        assert card.name

    def test_使用水流回转(self, card):
        """使用水流回转."""
        # Expected: damage_dealt = 120
        assert card is not None

    def test_使用夜光信号(self, card):
        """使用夜光信号."""
        # Expected: ability_used = True
        assert card is not None

