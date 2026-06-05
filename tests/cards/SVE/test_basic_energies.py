"""Level 1: 基本能量卡属性验证。"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
import pytest
from ptcg.core.card_registry import registry
from ptcg.core.enums import CardType, EnergyType, SuperType

BASIC_ENERGIES = [
    ("SVE-002", "Fire Energy", CardType.FIRE, EnergyType.BASIC, [CardType.FIRE]),
    ("SVE-004", "Lightning Energy", CardType.LIGHTNING, EnergyType.BASIC, [CardType.LIGHTNING]),
    ("SVE-005", "Psychic Energy", CardType.PSYCHIC, EnergyType.BASIC, [CardType.PSYCHIC]),
    ("SVE-007", "Darkness Energy", CardType.DARK, EnergyType.BASIC, [CardType.DARK]),
    ("SVE-008", "Metal Energy", CardType.METAL, EnergyType.BASIC, [CardType.METAL]),
]


def _check(cond, msg):
    assert cond, msg


@pytest.mark.unit
@pytest.mark.parametrize("cid,ename,ectype,een_type,eprov", BASIC_ENERGIES)
def test_basic_energy_attributes(cid, ename, ectype, een_type, eprov):
    card = registry.get(cid)()
    _check(card.name == ename, f"name: {ename} vs {card.name}")
    _check(card.set_name == "SVE", f"set: SVE vs {card.set_name}")
    _check(card.cardType == ectype, f"cardType: {ectype} vs {card.cardType}")
    _check(card.superType == SuperType.ENERGY, f"superType: ENERGY vs {card.superType}")
    _check(card.energyType == een_type, f"energyType: {een_type} vs {card.energyType}")
    _check(card.provides == eprov, f"provides: {eprov} vs {card.provides}")


@pytest.mark.unit
@pytest.mark.parametrize("cid", ["SVE-002", "SVE-004", "SVE-005", "SVE-007", "SVE-008"])
def test_energy_card_basics(cid):
    card = registry.get(cid)()
    assert card.superType == SuperType.ENERGY
    assert card.energyType == EnergyType.BASIC
    assert len(card.provides) > 0
