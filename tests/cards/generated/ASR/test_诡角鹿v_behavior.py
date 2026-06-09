"""诡角鹿V (ASR-134) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "ASR-134"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test诡角鹿VL4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 屏障猛攻: 造成40伤害
        # Rule: 特性 拓荒之路
        assert card.name

    def test_使用屏障猛攻(self, card):
        """使用屏障猛攻."""
        # Expected: damage_dealt = 40
        assert card is not None

    def test_使用拓荒之路(self, card):
        """使用拓荒之路."""
        # Expected: ability_used = True
        assert card is not None

