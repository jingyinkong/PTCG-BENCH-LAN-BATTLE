"""沙奈朵ex SVI-086 测试 — Tier 3 L1-L3."""
import pytest
from ptcg.core.card_registry import registry
from ptcg.core.enums import SuperType, Stage, CardType

CARD_ID = "SVI-086"


@pytest.fixture
def card():
    return registry.get(CARD_ID)()


class TestL1Structure:
    def test_base_attrs(self, card):
        assert card.name == "沙奈朵ex"
        assert card.hp == 310
        assert card.stage == Stage.STAGE_2
        assert card.superType == SuperType.POKEMON
        assert card.cardType == CardType.PSYCHIC
        assert card.prize == 2

    def test_has_ability(self, card):
        assert len(card.ability) > 0, "沙奈朵ex应有Psychic Embrace特性"

    def test_has_attacks(self, card):
        assert len(card.attacks) >= 1


class TestL2Actions:
    def test_generates_actions(self, card):
        import inspect
        source = inspect.getsource(type(card).get_actions)
        assert "AttackAction" in source
