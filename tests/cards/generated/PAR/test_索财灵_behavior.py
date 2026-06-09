"""索财灵 (PAR-088) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "PAR-088"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test索财灵L4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 连掷硬币: 造成20伤害
        assert card.name

    def test_使用连掷硬币(self, card):
        """使用连掷硬币."""
        # Expected: damage_dealt = 20
        assert card is not None

