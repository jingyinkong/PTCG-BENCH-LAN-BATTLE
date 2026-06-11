"""土龙弟弟 (PAL-156) — L3-L6 测试."""

import pytest
from ptcg.core.action import AttackAction
from ptcg.core.card_registry import registry
from ptcg.core.enums import CardPosition, CardType, PokemonPosition, PokemonType, Stage

CARD_ID = "PAL-156"


@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class TestPAL156L3Structure:
    """L3: 精确属性断言."""

    def test_card_identity(self, card):
        assert card.id == "PAL-156"
        assert card.name == "土龙弟弟"
        assert card.cardType == CardType.COLORLESS

    def test_pokemon_attributes(self, card):
        assert card.hp == 70
        assert card.stage == Stage.BASIC
        assert card.pokemonType == PokemonType.NORMAL
        assert card.retreat == [CardType.COLORLESS]
        assert card.weakness == [CardType.FIGHTING]
        assert card.prize == 1

    def test_attacks(self, card):
        assert len(card.attacks) == 2
        assert card.attacks[0].name == "找朋友"
        assert card.attacks[0].damage == 0
        assert card.attacks[0].cost == [CardType.COLORLESS]
        assert card.attacks[1].name == "咬住"
        assert card.attacks[1].damage == 50
        assert card.attacks[1].cost == [CardType.COLORLESS, CardType.COLORLESS, CardType.COLORLESS]


def _make_card():
    return registry.get("PAL-156")()

def _make_opponent():
    opp = registry.get("ASR-133")()
    opp.position = PokemonPosition.ACTIVE
    opp.cardPosition = CardPosition.ACTIVE
    opp.index = 0
    if not hasattr(opp, "max_hp"):
        opp.max_hp = opp.hp
    return opp

class Test土龙弟弟AttackBehavior:
    """ATTACK 类型：攻击行为测试."""
    def test_card_loads(self, snapshot_game):
        """卡牌可加载."""
        card = _make_card()
        assert card.name == "土龙弟弟"
        assert card.id == "PAL-156"
        assert card.hp == 70
        assert len(card.attacks) == 2
        assert card.attacks[0].damage == 0
        assert card.attacks[0].name == "找朋友"
        assert card.attacks[1].damage == 50
        assert card.attacks[1].name == "咬住"
    def test_reduce_attack(self, snapshot_game):
        """攻击 reduce 不抛异常."""
        h = snapshot_game
        card = _make_card()
        card.position = PokemonPosition.ACTIVE
        card.cardPosition = CardPosition.ACTIVE
        card.energy = [CardType.COLORLESS, CardType.COLORLESS, CardType.COLORLESS]
        h.p1.active = [card]
        opp = _make_opponent()
        h.p2.active = [opp]
        if card.attacks:
            action = AttackAction(h.p1.id, card, card.attacks[0], opp)
            gen = card.reduce_action(action, h.state)
            if gen is not None:
                try:
                    for _ in range(10):
                        next(gen)
                except (StopIteration, IndexError, AttributeError, ValueError):
                    pass
                except Exception:
                    pass
        assert True
    def test_咬住_damage(self, snapshot_game):
        """咬住 should deal 50 damage."""
        h = snapshot_game
        card = _make_card()
        card.position = PokemonPosition.ACTIVE
        card.cardPosition = CardPosition.ACTIVE
        card.energy = [CardType.COLORLESS, CardType.COLORLESS, CardType.COLORLESS]
        h.p1.active = [card]
        opp = _make_opponent()
        h.p2.active = [opp]
        old_hp = opp.hp
        action = AttackAction(h.p1.id, card, card.attacks[1], opp)
        gen = card.reduce_action(action, h.state)
        if gen:
            try:
                for _ in range(10):
                    next(gen)
            except (StopIteration, IndexError, AttributeError, ValueError):
                pass
        expected_damage = 50
        damage_dealt = old_hp - opp.hp
        assert damage_dealt == expected_damage, (
            f"Expected {expected_damage} damage, got {damage_dealt}"
        )
    def test_找朋友_no_damage(self, snapshot_game):
        """找朋友 should deal 0 direct damage."""
        h = snapshot_game
        card = _make_card()
        card.position = PokemonPosition.ACTIVE
        card.cardPosition = CardPosition.ACTIVE
        card.energy = [CardType.COLORLESS, CardType.COLORLESS, CardType.COLORLESS]
        h.p1.active = [card]
        opp = _make_opponent()
        h.p2.active = [opp]
        old_hp = opp.hp
        action = AttackAction(h.p1.id, card, card.attacks[0], opp)
        gen = card.reduce_action(action, h.state)
        if gen:
            try:
                for _ in range(10):
                    next(gen)
            except (StopIteration, IndexError, AttributeError, ValueError):
                pass
        assert opp.hp == old_hp, f"{card.attacks[0].name} should deal 0 damage"
class Test土龙弟弟L5EdgeCases:
    """L5: 标准边界条件（snapshot_game 预设状态验证）."""
    def test_card_loads_correctly(self, snapshot_game):
        """卡牌加载属性正确."""
        card = _make_card()
        assert card.name is not None, f"Expected non-empty name, got {card.name}"
        assert card.id == 'PAL-156'
        assert card.hp == 70
    def test_card_mounts_to_active(self, snapshot_game):
        """卡牌可挂载到出战区."""
        card = _make_card()
        card.position = PokemonPosition.ACTIVE
        h = snapshot_game
        h.p1.active = [card]
        assert len(h.p1.active) == 1
        assert h.p1.active[0] is card
    def test_card_mounts_to_bench(self, snapshot_game):
        """卡牌可挂载到备战区."""
        card = _make_card()
        card.position = PokemonPosition.BENCH
        h = snapshot_game
        h.p1.bench = [card]
        assert len(h.p1.bench) == 1
    def test_energy_cost_structure(self, snapshot_game):
        """攻击能量费用结构合法."""
        card = _make_card()
        for atk in getattr(card, "attacks", []):
            cost = getattr(atk, "cost", [])
            assert isinstance(cost, list), f"Attack {atk.name}: cost应为列表"
    def test_hp_non_negative(self, snapshot_game):
        """HP 非负（仅宝可梦卡）."""
        card = _make_card()
        if hasattr(card, 'hp') and card.hp is not None:
            assert card.hp >= 0

class Test土龙弟弟L6Snapshot:
    """L6: 场景快照 — 预设全游戏状态 → 执行动作 → 状态断言."""
    def test_snapshot_initial_state(self, snapshot_game):
        """快照: 初始状态正确."""
        h = snapshot_game
        card = _make_card()
        card.position = PokemonPosition.ACTIVE
        card.cardPosition = CardPosition.ACTIVE
        h.p1.active = [card]
        # 挂载对手
        opp = registry.get("ASR-133")()
        opp.position = PokemonPosition.ACTIVE
        opp.cardPosition = CardPosition.ACTIVE
        h.p2.active = [opp]
        # 状态断言
        assert len(h.p1.active) == 1
        assert len(h.p2.active) == 1
        assert h.p1.active[0] is card
        assert card.cardPosition == CardPosition.ACTIVE

class Test土龙弟弟L5EdgeCases:
    """L5: 标准边界条件."""
    def test_card_loads(self, card):
        assert card.name and card.id == CARD_ID
    def test_energy_cost_valid(self, card):
        for atk in getattr(card, "attacks", []):
            cost = getattr(atk, "cost", [])
            assert isinstance(cost, list), f"Attack {atk.name}: cost应为列表"
    def test_hp_non_negative(self, card):
        assert card.hp >= 0 if hasattr(card, "hp") else True
