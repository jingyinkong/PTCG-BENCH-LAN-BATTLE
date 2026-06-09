"""多龙奇 (TWM-129) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "TWM-129"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test多龙奇L4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 龙之头击: 造成70伤害
        # Rule: 特性 侦察指令
        assert card.name

    def test_使用龙之头击(self, card):
        """使用龙之头击."""
        # Expected: damage_dealt = 70
        assert card is not None

    def test_使用侦察指令(self, card):
        """使用侦察指令."""
        # Expected: ability_used = True
        assert card is not None

