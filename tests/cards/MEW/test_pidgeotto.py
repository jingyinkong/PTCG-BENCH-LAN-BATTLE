"""Level 2: Pidgeotto MEW-017 属性验证。"""
import pytest
from ptcg.core.card_registry import registry
from ptcg.core.enums import CardType, PokemonType, Stage, SuperType

@pytest.mark.unit
def test_pidgeotto_attributes():
    card = registry.get("MEW-017")()
    assert card.name == "比比鸟"
    assert card.hp == 80
    assert card.pokemonType == PokemonType.NORMAL
    assert card.stage == Stage.STAGE_1
    assert card.cardType == CardType.COLORLESS
    assert card.superType == SuperType.POKEMON
    assert card.retreat == []  # Fixed: was [COLORLESS]
    assert card.weakness == [CardType.LIGHTNING]
    assert card.resistance == [CardType.FIGHTING]
    assert card.prize == 1
    assert len(card.attacks) == 1
    assert card.attacks[0].name == "Flap"
    assert card.attacks[0].damage == 20
    assert card.attacks[0].cost == [CardType.COLORLESS]
