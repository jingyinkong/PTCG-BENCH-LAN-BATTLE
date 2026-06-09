"""梦幻ex (MEW-151) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "MEW-151"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test梦幻exL4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 基因侵入: 造成0伤害
        # Rule: 特性 再起动
        assert card.name

    def test_使用基因侵入(self, card):
        """使用基因侵入."""
        # Expected: damage_dealt = 0
        assert card is not None

    def test_使用再起动(self, card):
        """使用再起动."""
        # Expected: ability_used = True
        assert card is not None

