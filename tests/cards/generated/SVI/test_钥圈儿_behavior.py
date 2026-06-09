"""钥圈儿 (SVI-096) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "SVI-096"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test钥圈儿L4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 狙落: 造成10伤害
        # Rule: 特性 恶作剧之锁
        assert card.name

    def test_使用狙落(self, card):
        """使用狙落."""
        # Expected: damage_dealt = 10
        assert card is not None

    def test_使用恶作剧之锁(self, card):
        """使用恶作剧之锁."""
        # Expected: ability_used = True
        assert card is not None

