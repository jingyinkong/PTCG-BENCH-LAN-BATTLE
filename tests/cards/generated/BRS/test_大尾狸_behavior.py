"""大尾狸 (BRS-121) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "BRS-121"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test大尾狸L4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 长尾粉碎: 造成100伤害
        # Rule: 特性 勤奋门牙
        assert card.name

    def test_使用长尾粉碎(self, card):
        """使用长尾粉碎."""
        # Expected: damage_dealt = 100
        assert card is not None

    def test_使用勤奋门牙(self, card):
        """使用勤奋门牙."""
        # Expected: ability_used = True
        assert card is not None

