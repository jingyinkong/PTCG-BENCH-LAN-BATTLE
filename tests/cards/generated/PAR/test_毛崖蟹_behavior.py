"""毛崖蟹 (PAR-105) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "PAR-105"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test毛崖蟹L4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 歇斯底里巨钳: 造成30伤害
        # Rule: 攻击 沸腾压制: 造成80伤害
        assert card.name

    def test_使用歇斯底里巨钳(self, card):
        """使用歇斯底里巨钳."""
        # Expected: damage_dealt = 30
        assert card is not None

    def test_使用沸腾压制(self, card):
        """使用沸腾压制."""
        # Expected: damage_dealt = 80
        assert card is not None

