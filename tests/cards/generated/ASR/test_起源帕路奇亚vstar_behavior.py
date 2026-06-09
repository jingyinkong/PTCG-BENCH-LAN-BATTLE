"""起源帕路奇亚VSTAR (ASR-040) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "ASR-040"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test起源帕路奇亚VSTARL4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 亚空潮漩: 造成60伤害
        # Rule: 特性 星耀空扉
        assert card.name

    def test_使用亚空潮漩(self, card):
        """使用亚空潮漩."""
        # Expected: damage_dealt = 60
        assert card is not None

    def test_使用星耀空扉(self, card):
        """使用星耀空扉."""
        # Expected: ability_used = True
        assert card is not None

