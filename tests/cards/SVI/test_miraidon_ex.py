"""蜜勒顿ex SVI-081 测试 — Tier 3 L1-L3."""
import pytest
from ptcg.core.card_registry import registry
from ptcg.core.enums import SuperType, Stage, CardType
from ptcg.core.ability import ActiveAbility

CARD_ID = "SVI-081"


@pytest.fixture
def card():
    return registry.get(CARD_ID)()


class TestL1Structure:
    def test_base_attrs(self, card):
        assert card.name == "密勒顿ex"
        assert card.hp == 220
        assert card.stage == Stage.BASIC
        assert card.superType == SuperType.POKEMON
        assert card.cardType == CardType.LIGHTNING
        assert card.prize == 2

    def test_has_attacks(self, card):
        assert len(card.attacks) >= 1


class TestL2Actions:
    def test_generates_actions(self, card):
        import inspect
        source = inspect.getsource(type(card).get_actions)
        assert "AttackAction" in source
