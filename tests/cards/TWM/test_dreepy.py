"""Level 2: Dreepy TWM-128 属性验证。"""
import pytest
from ptcg.core.card_registry import registry
from ptcg.core.enums import SuperType, Stage

@pytest.mark.unit
def test_dreepy_attributes():
    card = registry.get("TWM-128")()
    assert card.name == "多龙梅西亚"
    assert card.hp == 70
    assert card.stage == Stage.BASIC
    assert card.superType == SuperType.POKEMON
    assert len(card.attacks) >= 1
