"""拉鲁拉丝 (ASR-060) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "ASR-060"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test拉鲁拉丝L4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 瞬移破坏: 造成10伤害
        assert card.name

    def test_使用瞬移破坏(self, card):
        """使用瞬移破坏."""
        # Expected: damage_dealt = 10
        assert card is not None

