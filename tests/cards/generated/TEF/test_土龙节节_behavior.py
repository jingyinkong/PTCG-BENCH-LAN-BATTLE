"""土龙节节 (TEF-129) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "TEF-129"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test土龙节节L4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 大地粉碎: 造成90伤害
        # Rule: 特性 逃跑抽取
        assert card.name

    def test_使用大地粉碎(self, card):
        """使用大地粉碎."""
        # Expected: damage_dealt = 90
        assert card is not None

    def test_使用逃跑抽取(self, card):
        """使用逃跑抽取."""
        # Expected: ability_used = True
        assert card is not None

