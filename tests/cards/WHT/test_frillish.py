"""Level 2: Frillish WHT-044 属性验证。"""
import pytest
from ptcg.core.card_registry import registry
from ptcg.core.enums import CardType, PokemonType, Stage, SuperType

@pytest.mark.unit
def test_frillish_attributes():
    card = registry.get("WHT-044")()
    assert card.name == "轻飘飘"
    assert card.hp == 80
    assert card.stage == Stage.BASIC
    assert card.superType == SuperType.POKEMON
    assert card.retreat == [CardType.COLORLESS, CardType.COLORLESS, CardType.COLORLESS]
    assert len(card.attacks) >= 1
