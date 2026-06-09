"""批量 Tier 覆盖测试 — 自动验证所有卡牌的L1-L3结构完整性.

通过 CardRegistry 动态加载所有卡牌，按复杂度分级自动验证，
无需硬编码卡牌属性。
"""
import inspect
import pytest
from ptcg.core.card_registry import registry
from ptcg.core.enums import SuperType
from ptcg.core.card import EnergyCard, PokemonCard, ItemCard, SupporterCard, ToolCard
from ptcg.core.ability import ActiveAbility

registry._ensure_loaded()
ALL_IDS = sorted(registry._cards.keys())


def _make_card(card_id):
    try:
        return registry.get(card_id)()
    except Exception:
        return None


def _tier(card):
    if card is None:
        return 0
    if getattr(card, 'prize', 1) >= 2:
        return 3
    if isinstance(card, EnergyCard):
        return 1
    if isinstance(card, (ItemCard, SupporterCard, ToolCard)):
        return 2
    if isinstance(card, PokemonCard):
        has_effect = False
        if hasattr(card, 'ability') and card.ability:
            for ab in card.ability:
                if isinstance(ab, ActiveAbility):
                    has_effect = True
        if hasattr(card, 'attacks') and card.attacks:
            for atk in card.attacks:
                if atk.text and atk.text.strip():
                    has_effect = True
        return 2 if has_effect else 1
    return 2


def _all_of_tier(t):
    return [(cid, c) for cid in ALL_IDS if (c := _make_card(cid)) and _tier(c) == t]


def _pokemon_of_tier(t):
    return [(cid, c) for cid, c in _all_of_tier(t) if isinstance(c, PokemonCard)]


def _items_of_tier(t):
    return [(cid, c) for cid, c in _all_of_tier(t) if isinstance(c, ItemCard)]


def _supporters_of_tier(t):
    return [(cid, c) for cid, c in _all_of_tier(t) if isinstance(c, SupporterCard)]


def _energies():
    return [(cid, c) for cid, c in _all_of_tier(1) if isinstance(c, EnergyCard)]


# ==================== L1: Structure ====================

class TestL1AllCards:
    """所有卡牌基础结构."""

    @pytest.mark.parametrize("card_id,card", _all_of_tier(1) + _all_of_tier(2) + _all_of_tier(3))
    def test_instantiates_with_id(self, card_id, card):
        assert card.id == card_id
        assert card.name

    @pytest.mark.parametrize("card_id,card", _pokemon_of_tier(1) + _pokemon_of_tier(2) + _pokemon_of_tier(3))
    def test_pokemon_has_required(self, card_id, card):
        assert card.hp > 0, f"{card_id}: hp 应 > 0"
        assert hasattr(card, 'attacks')
        assert hasattr(card, 'retreat')

    @pytest.mark.parametrize("card_id,card", _energies())
    def test_energy_has_provides(self, card_id, card):
        assert hasattr(card, 'provides'), f"{card_id}: 缺少 provides"


# ==================== L2: Actions ====================

class TestL2Tier2And3:
    """Tier 2/3 Action 生成."""

    @pytest.mark.parametrize("card_id,card", _all_of_tier(2) + _all_of_tier(3))
    def test_get_actions_implemented(self, card_id, card):
        source = inspect.getsource(type(card).get_actions)
        assert len(source) > 30, f"{card_id}: get_actions 实现疑似继承/未覆盖"

    @pytest.mark.parametrize("card_id,card", _items_of_tier(2) + _items_of_tier(3))
    def test_item_use_item_action(self, card_id, card):
        source = inspect.getsource(type(card).get_actions)
        assert "UseItemAction" in source, f"{card_id}: 应生成 UseItemAction"

    @pytest.mark.parametrize("card_id,card", _supporters_of_tier(2) + _supporters_of_tier(3))
    def test_supporter_action(self, card_id, card):
        source = inspect.getsource(type(card).get_actions)
        assert "UseSupporterAction" in source, f"{card_id}: 应生成 UseSupporterAction"

    @pytest.mark.parametrize("card_id,card",
        _pokemon_of_tier(2) + _pokemon_of_tier(3))
    def test_pokemon_attack_action(self, card_id, card):
        source = inspect.getsource(type(card).get_actions)
        assert "AttackAction" in source, f"{card_id}: 应生成 AttackAction"


# ==================== L3: Handler ====================

class TestL3Tier2And3:
    """Tier 2/3 Action 处理."""

    @pytest.mark.parametrize("card_id,card", _all_of_tier(2) + _all_of_tier(3))
    def test_reduce_action_implemented(self, card_id, card):
        source = inspect.getsource(type(card).reduce_action)
        assert len(source) > 30, f"{card_id}: reduce_action 疑似继承/未覆盖"

    @pytest.mark.parametrize("card_id,card", _items_of_tier(2) + _items_of_tier(3))
    def test_item_handles_use_item(self, card_id, card):
        source = inspect.getsource(type(card).reduce_action)
        assert "UseItemAction" in source, f"{card_id}: 应处理 UseItemAction"

    @pytest.mark.parametrize("card_id,card",
        _pokemon_of_tier(2) + _pokemon_of_tier(3))
    def test_pokemon_handles_attack(self, card_id, card):
        source = inspect.getsource(type(card).reduce_action)
        assert "AttackAction" in source, f"{card_id}: 应处理 AttackAction"
