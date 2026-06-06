"""全量卡牌属性验证 — 覆盖所有已注册卡牌的基本属性和结构完整性。

P0 回归测试：引擎变更/卡牌基类修改导致属性异常时立即捕获。
"""

import pytest
from ptcg.core.card import EnergyCard, PokemonCard, TrainerCard
from ptcg.core.card_registry import registry
from ptcg.core.enums import EnergyType, PokemonRule, PokemonType, Stage, SuperType, TrainerType

registry._ensure_loaded()
ALL_CARD_IDS = sorted(registry.list_all())


# ============================================================
# 全量结构完整性
# ============================================================


@pytest.mark.integration
@pytest.mark.parametrize("card_id", ALL_CARD_IDS)
def test_card_has_required_identity_fields(card_id):
    """验证每张卡都有必需的标识字段。"""
    card = registry.get(card_id)()
    assert card.name, f"{card_id}: empty name"
    assert card.set_name, f"{card_id}: empty set_name"
    assert card.number, f"{card_id}: empty number"
    assert card.id == f"{card.set_name}-{card.number}", (
        f"{card_id}: id mismatch: '{card.id}' vs '{card.set_name}-{card.number}'"
    )
    assert card.superType in SuperType, f"{card_id}: invalid superType"


@pytest.mark.integration
@pytest.mark.parametrize("card_id", ALL_CARD_IDS)
def test_card_has_required_methods(card_id):
    """验证每张卡都实现了必需的引擎接口。"""
    card = registry.get(card_id)()
    assert callable(getattr(card, "get_actions", None)), f"{card_id}: missing get_actions"
    assert callable(getattr(card, "reduce_action", None)), f"{card_id}: missing reduce_action"


@pytest.mark.integration
@pytest.mark.parametrize("card_id", ALL_CARD_IDS)
def test_card_to_dict_and_get_info(card_id):
    """验证 to_dict() 和 get_info() 不抛异常。"""
    card = registry.get(card_id)()
    info = card.get_info()
    assert isinstance(info, dict), f"{card_id}: get_info() not dict"
    assert "name" in info, f"{card_id}: get_info() missing name"
    d = card.to_dict()
    assert isinstance(d, dict), f"{card_id}: to_dict() not dict"


# ============================================================
# Pokemon 卡
# ============================================================

ALL_POKEMON_IDS = sorted([
    cid for cid in ALL_CARD_IDS
    if issubclass(registry.get(cid), PokemonCard)
])


@pytest.mark.integration
@pytest.mark.parametrize("card_id", ALL_POKEMON_IDS)
def test_pokemon_hp_range(card_id):
    """验证 Pokemon HP 在合理范围内。"""
    card = registry.get(card_id)()
    assert card.hp > 0, f"{card_id}: hp={card.hp}"
    assert card.hp <= 340, f"{card_id}: hp={card.hp} > max"


@pytest.mark.integration
@pytest.mark.parametrize("card_id", ALL_POKEMON_IDS)
def test_pokemon_retreat_cost(card_id):
    """验证撤退费用合法。"""
    card = registry.get(card_id)()
    assert len(card.retreat) <= 5, f"{card_id}: retreat > 5"


@pytest.mark.integration
@pytest.mark.parametrize("card_id", ALL_POKEMON_IDS)
def test_pokemon_prize_value(card_id):
    """验证 prize 值合法。"""
    card = registry.get(card_id)()
    assert card.prize in (1, 2, 3), f"{card_id}: prize={card.prize}"


@pytest.mark.integration
@pytest.mark.parametrize("card_id", ALL_POKEMON_IDS)
def test_pokemon_attacks_valid(card_id):
    """验证攻击定义完整性。"""
    card = registry.get(card_id)()
    assert hasattr(card, "attacks"), f"{card_id}: missing attacks"
    for i, atk in enumerate(card.attacks):
        assert atk.name, f"{card_id} atk[{i}]: empty name"
        assert len(atk.cost) <= 5, f"{card_id} atk[{i}]: cost > 5"
        assert hasattr(atk, "damage"), f"{card_id} atk[{i}]: missing damage"


@pytest.mark.integration
@pytest.mark.parametrize("card_id", ALL_POKEMON_IDS)
def test_pokemon_stage_consistent(card_id):
    """验证进化阶段一致性：STAGE_2 必须有 evolveFrom。"""
    card = registry.get(card_id)()
    if card.stage == Stage.STAGE_2:
        assert hasattr(card, "evolveFrom"), f"{card_id}: STAGE_2 missing evolveFrom"
        assert len(card.evolveFrom) >= 1, f"{card_id}: STAGE_2 evolveFrom empty"


# ============================================================
# Energy 卡
# ============================================================

ALL_ENERGY_IDS = sorted([
    cid for cid in ALL_CARD_IDS
    if issubclass(registry.get(cid), EnergyCard)
])


@pytest.mark.integration
@pytest.mark.parametrize("card_id", ALL_ENERGY_IDS)
def test_energy_has_provides(card_id):
    """验证能量卡有 provides 和 energyType。"""
    card = registry.get(card_id)()
    assert hasattr(card, "provides"), f"{card_id}: missing provides"
    assert len(card.provides) >= 1, f"{card_id}: provides empty"
    assert hasattr(card, "energyType"), f"{card_id}: missing energyType"


# ============================================================
# Trainer 卡
# ============================================================

ALL_TRAINER_IDS = sorted([
    cid for cid in ALL_CARD_IDS
    if issubclass(registry.get(cid), TrainerCard)
    and not issubclass(registry.get(cid), EnergyCard)
])


@pytest.mark.integration
@pytest.mark.parametrize("card_id", ALL_TRAINER_IDS)
def test_trainer_has_type(card_id):
    """验证训练家卡有有效的 trainerType。"""
    card = registry.get(card_id)()
    assert hasattr(card, "trainerType"), f"{card_id}: missing trainerType"
    assert card.trainerType in TrainerType, f"{card_id}: invalid trainerType"


# ============================================================
# 交叉验证
# ============================================================


def test_card_ids_are_unique():
    """验证所有卡牌 ID 唯一。"""
    seen = {}
    for cid in ALL_CARD_IDS:
        card = registry.get(cid)()
        if card.id in seen:
            pytest.fail(f"Duplicate card id: {card.id} ({cid} and {seen[card.id]})")
        seen[card.id] = cid


def test_no_two_cards_same_set_and_number():
    """验证同一系列中没有重复编号。"""
    set_numbers = {}
    for cid in ALL_CARD_IDS:
        card = registry.get(cid)()
        key = (card.set_name, card.number)
        if key in set_numbers:
            pytest.fail(f"Duplicate {card.set_name}-{card.number}: {cid} and {set_numbers[key]}")
        set_numbers[key] = cid
