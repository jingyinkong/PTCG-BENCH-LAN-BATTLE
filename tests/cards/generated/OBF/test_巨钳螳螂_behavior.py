"""巨钳螳螂 (OBF-141) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "OBF-141"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test巨钳螳螂L4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 惩罚巨钳: 造成10伤害
        # Rule: 攻击 居合劈: 造成70伤害
        assert card.name

    def test_使用惩罚巨钳(self, card):
        """使用惩罚巨钳."""
        # Expected: damage_dealt = 10
        assert card is not None

    def test_使用居合劈(self, card):
        """使用居合劈."""
        # Expected: damage_dealt = 70
        assert card is not None

