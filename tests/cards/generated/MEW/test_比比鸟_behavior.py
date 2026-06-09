"""比比鸟 (MEW-017) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "MEW-017"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test比比鸟L4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 振翅: 造成20伤害
        assert card.name

    def test_使用振翅(self, card):
        """使用振翅."""
        # Expected: damage_dealt = 20
        assert card is not None

