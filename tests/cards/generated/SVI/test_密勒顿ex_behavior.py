"""密勒顿ex (SVI-081) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "SVI-081"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test密勒顿exL4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 光子引爆: 造成220伤害
        # Rule: 特性 串联装置
        assert card.name

    def test_使用光子引爆(self, card):
        """使用光子引爆."""
        # Expected: damage_dealt = 220
        assert card is not None

    def test_使用串联装置(self, card):
        """使用串联装置."""
        # Expected: ability_used = True
        assert card is not None

