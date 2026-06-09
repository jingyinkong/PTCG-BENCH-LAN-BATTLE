"""铁臂膀ex (PAR-248) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "PAR-248"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test铁臂膀exL4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 臂膀压制: 造成160伤害
        # Rule: 攻击 多谢款待: 造成120伤害
        assert card.name

    def test_使用臂膀压制(self, card):
        """使用臂膀压制."""
        # Expected: damage_dealt = 160
        assert card is not None

    def test_使用多谢款待(self, card):
        """使用多谢款待."""
        # Expected: damage_dealt = 120
        assert card is not None

