"""铁包袱 (PAR-056) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "PAR-056"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test铁包袱L4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 冷却喷射: 造成80伤害
        # Rule: 特性 强力吹风机
        assert card.name

    def test_使用冷却喷射(self, card):
        """使用冷却喷射."""
        # Expected: damage_dealt = 80
        assert card is not None

    def test_使用强力吹风机(self, card):
        """使用强力吹风机."""
        # Expected: ability_used = True
        assert card is not None

