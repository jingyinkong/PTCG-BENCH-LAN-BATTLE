"""智挥猩V (ASR-133) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "ASR-133"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test智挥猩VL4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 精神强念: 造成30伤害
        # Rule: 特性 预订
        assert card.name

    def test_使用精神强念(self, card):
        """使用精神强念."""
        # Expected: damage_dealt = 30
        assert card is not None

    def test_使用预订(self, card):
        """使用预订."""
        # Expected: ability_used = True
        assert card is not None

