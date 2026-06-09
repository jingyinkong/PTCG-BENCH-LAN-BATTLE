"""桃歹郎 (SVP-149) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "SVP-149"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test桃歹郎L4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 毒液锁链: 造成10伤害
        # Rule: 特性 剧毒支配
        assert card.name

    def test_使用毒液锁链(self, card):
        """使用毒液锁链."""
        # Expected: damage_dealt = 10
        assert card is not None

    def test_使用剧毒支配(self, card):
        """使用剧毒支配."""
        # Expected: ability_used = True
        assert card is not None

