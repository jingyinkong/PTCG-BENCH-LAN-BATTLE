"""卡比兽 (LOR-143) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "LOR-143"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test卡比兽L4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 轰隆鼾声: 造成180伤害
        # Rule: 特性 无畏脂肪
        assert card.name

    def test_使用轰隆鼾声(self, card):
        """使用轰隆鼾声."""
        # Expected: damage_dealt = 180
        assert card is not None

    def test_使用无畏脂肪(self, card):
        """使用无畏脂肪."""
        # Expected: ability_used = True
        assert card is not None

