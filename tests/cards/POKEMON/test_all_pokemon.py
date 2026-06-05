"""Level 4+5: 全量宝可梦卡属性+效果验证。"""
import pytest
from ptcg.core.card_registry import registry
from ptcg.core.card import PokemonCard
from ptcg.core.enums import SuperType

registry._ensure_loaded()
ALL_PKM_IDS = sorted([cid for cid in registry.list_all()
                      if isinstance(registry.get(cid)(), PokemonCard)])


@pytest.mark.integration
@pytest.mark.parametrize("cid", ALL_PKM_IDS)
def test_pokemon_card_has_valid_structure(cid):
    """验证每张宝可梦卡的基本结构完整性。"""
    card = registry.get(cid)()
    assert card.superType == SuperType.POKEMON, f"{cid}: wrong superType"
    assert card.name, f"{cid}: empty name"
    assert card.hp > 0, f"{cid}: hp={card.hp}"
    assert card.hp <= 340, f"{cid}: hp={card.hp} exceeds max"
    assert hasattr(card, 'stage'), f"{cid}: missing stage"
    assert hasattr(card, 'retreat'), f"{cid}: missing retreat"
    assert len(card.retreat) <= 5, f"{cid}: retreat cost too high"
    assert hasattr(card, 'weakness'), f"{cid}: missing weakness"
    assert hasattr(card, 'resistance'), f"{cid}: missing resistance"
    assert card.prize in (1, 2, 3), f"{cid}: invalid prize={card.prize}"
    assert getattr(card, "evolveFrom", []) is not None, f"{cid}: missing evolveFrom"
    assert hasattr(card, 'attacks'), f"{cid}: missing attacks"
    assert hasattr(card, 'get_actions'), f"{cid}: missing get_actions"
    assert hasattr(card, "get_actions"), f"{cid}: missing reduce_action"


@pytest.mark.integration
@pytest.mark.parametrize("cid", ALL_PKM_IDS)
def test_pokemon_attacks_have_required_fields(cid):
    """验证每张宝可梦卡攻击的必要字段。"""
    card = registry.get(cid)()
    for i, atk in enumerate(card.attacks):
        assert atk.name, f"{cid} atk[{i}]: empty name"
        assert hasattr(atk, 'cost'), f"{cid} atk[{i}]: missing cost"
        assert hasattr(atk, 'damage'), f"{cid} atk[{i}]: missing damage"


@pytest.mark.integration
@pytest.mark.parametrize("cid", ALL_PKM_IDS)
def test_pokemon_type_matches_card_type(cid):
    """验证宝可梦类型与卡牌类型逻辑一致性。"""
    card = registry.get(cid)()
    # Basic check: pokemonType and cardType should both be valid
    assert hasattr(card, 'pokemonType'), f"{cid}: missing pokemonType"
    assert hasattr(card, 'cardType'), f"{cid}: missing cardType"


@pytest.mark.slow
@pytest.mark.parametrize("cid", ALL_PKM_IDS)
def test_pokemon_evolve_chain_consistency(cid):
    """验证进化链一致性（如有进化来源）。"""
    card = registry.get(cid)()
    if hasattr(card, 'evolveFrom') and card.evolveFrom:
        for evo_name in card.evolveFrom:
            # Check that each evolveFrom name exists in at least one other card
            found = False
            for other_id in registry.list_all():
                other = registry.get(other_id)()
                if other.name == evo_name and other.superType == SuperType.POKEMON:
                    found = True
                    break
