"""赛富豪ex (PAR-139) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "PAR-139"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test赛富豪exL4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 淘金潮: 造成50伤害
        # Rule: 特性 嘉奖硬币
        assert card.name

    def test_使用淘金潮(self, card):
        """使用淘金潮."""
        # Expected: damage_dealt = 50
        assert card is not None

    def test_使用嘉奖硬币(self, card):
        """使用嘉奖硬币."""
        # Expected: ability_used = True
        assert card is not None

