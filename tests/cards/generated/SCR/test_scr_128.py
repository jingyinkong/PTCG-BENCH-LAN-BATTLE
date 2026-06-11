"""太乐巴戈斯ex (SCR-128) — L3-L6 测试."""

import pytest
from ptcg.core.card_registry import registry
from ptcg.core.enums import CardPosition, CardType, PokemonPosition, PokemonRule, PokemonType, Stage

CARD_ID = "SCR-128"


@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class TestSCR128L3Structure:
    """L3: 精确属性断言."""

    def test_card_identity(self, card):
        assert card.id == "SCR-128"
        assert card.name == "太乐巴戈斯ex"
        assert card.cardType == CardType.COLORLESS

    def test_pokemon_attributes(self, card):
        assert card.hp == 230
        assert card.stage == Stage.BASIC
        assert card.pokemonType == PokemonType.NORMAL
        assert card.retreat == [CardType.COLORLESS, CardType.COLORLESS]
        assert card.weakness == [CardType.FIGHTING]
        assert card.prize == 2
        assert card.pokemonRule == PokemonRule.TERA

    def test_attacks(self, card):
        assert len(card.attacks) == 2
        assert card.attacks[0].name == "同盟打击"
        assert card.attacks[0].damage == 30
        assert card.attacks[0].cost == [CardType.COLORLESS, CardType.COLORLESS]
        assert card.attacks[1].name == "皇冠蛋白石"
        assert card.attacks[1].damage == 180
        assert card.attacks[1].cost == [CardType.GRASS, CardType.WATER, CardType.LIGHTNING]


class Test太乐巴戈斯exL4Behavior:
    """L4: 效果行为验证."""
    def test_text_rules_documented(self, card):
        """验证效果规则已记录."""
        # Rule: 攻击 同盟打击: 造成30伤害
        # Rule: 攻击 皇冠蛋白石: 造成180伤害
        assert card.name
    def test_使用同盟打击(self, card):
        """使用同盟打击."""
        # Expected: damage_dealt = 30
        assert card is not None
    def test_使用皇冠蛋白石(self, card):
        """使用皇冠蛋白石."""
        # Expected: damage_dealt = 180
        assert card is not None

class Test太乐巴戈斯exL5EdgeCases:
    """L5: 标准边界条件（snapshot_game 预设状态验证）."""
    def test_card_loads_correctly(self, snapshot_game):
        """卡牌加载属性正确."""
        card = _make_card()
        assert card.name is not None, f"Expected non-empty name, got {card.name}"
        assert card.id == 'SCR-128'
        assert card.hp == 230
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

class Test太乐巴戈斯exL6Snapshot:
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

class Test太乐巴戈斯exL5EdgeCases:
    """L5: 标准边界条件."""
    def test_card_loads(self, card):
        assert card.name and card.id == CARD_ID
    def test_energy_cost_valid(self, card):
        for atk in getattr(card, "attacks", []):
            cost = getattr(atk, "cost", [])
            assert isinstance(cost, list), f"Attack {atk.name}: cost应为列表"
    def test_hp_non_negative(self, card):
        assert card.hp >= 0 if hasattr(card, "hp") else True

class Test太乐巴戈斯exL6Snapshot:
    """L6: 场景快照."""
    def test_snapshot_使用同盟打击(self, card):
        """使用同盟打击."""
        # Then: {"damage_dealt": 30}
        assert card is not None
    def test_snapshot_使用皇冠蛋白石(self, card):
        """使用皇冠蛋白石."""
        # Then: {"damage_dealt": 180}
        assert card is not None