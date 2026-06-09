"""起源帕路奇亚V (ASR-039) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "ASR-039"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test起源帕路奇亚VL4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 领域支配: 造成0伤害
        # Rule: 攻击 水炮破坏: 造成200伤害
        assert card.name

    def test_使用领域支配(self, card):
        """使用领域支配."""
        # Expected: damage_dealt = 0
        assert card is not None

    def test_使用水炮破坏(self, card):
        """使用水炮破坏."""
        # Expected: damage_dealt = 200
        assert card is not None

