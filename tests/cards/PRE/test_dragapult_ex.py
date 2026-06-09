"""多龙巴鲁托ex PRE-073 测试 — Tier 3 L1-L3."""
import pytest
from ptcg.core.card_registry import registry
from ptcg.core.enums import SuperType, Stage, CardType

CARD_ID = "PRE-073"


@pytest.fixture
def card():
    return registry.get(CARD_ID)()


class TestL1Structure:
    def test_base_attrs(self, card):
        assert card.name == "多龙巴鲁托ex"
        assert card.hp == 320
        assert card.stage == Stage.STAGE_2
        assert card.superType == SuperType.POKEMON
        assert card.cardType == CardType.DRAGON
        assert card.prize == 2

    def test_has_attacks(self, card):
        assert len(card.attacks) >= 1


class TestL2Actions:
    def test_generates_actions(self, card):
        import inspect
        source = inspect.getsource(type(card).get_actions)
        assert "AttackAction" in source
