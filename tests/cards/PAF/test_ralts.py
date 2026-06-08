"""Level 2: Ralts PAF-027 属性验证。"""
import pytest
from ptcg.core.card_registry import registry
from ptcg.core.enums import CardType, PokemonType, Stage, SuperType

@pytest.mark.unit
def test_ralts_attributes():
    card = registry.get("PAF-027")()
    assert card.name == "拉鲁拉丝"
    assert card.hp == 70
    assert card.stage == Stage.BASIC
    assert card.superType == SuperType.POKEMON
    assert len(card.attacks) >= 1
