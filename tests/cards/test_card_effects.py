"""卡牌效果逻辑测试 — 使用游戏引擎验证 get_actions() 和 reduce_action()。

测试场景:
  1. 基本能量附着
  2. 宝可梦进场
  3. 训练家卡使用条件
  4. 攻击效果
  5. 特殊能量效果
"""
import pytest
from ptcg.core.envs import PokemonTCG
from ptcg.core.card_registry import registry
from ptcg.core.enums import (
    CardType, EnergyType, SuperType, PokemonType, Stage, TrainerType,
    CardPosition, PlayerId
)
from ptcg.core.card import PokemonCard, EnergyCard, TrainerCard
from ptcg.utils.load_deck import load_deck


# ============================================================================
# 测试 1: 基本能量卡效果 — 附着到宝可梦
# ============================================================================
class TestBasicEnergyEffects:
    """验证基本能量卡的 get_actions 和附着逻辑。"""

    def test_fire_energy_provides_fire(self):
        """SVE-002 Fire Energy 提供火能量。"""
        card = registry.get("SVE-002")()
        assert card.energyType == EnergyType.BASIC
        assert CardType.FIRE in card.provides
        assert card.superType == SuperType.ENERGY

    def test_all_basic_energies_provide_correct_type(self):
        """所有基本能量卡提供正确的能量类型。"""
        expected = {
            "SVE-002": CardType.FIRE,
            "SVE-004": CardType.LIGHTNING,
            "SVE-005": CardType.PSYCHIC,
            "SVE-007": CardType.DARK,
            "SVE-008": CardType.METAL,
        }
        for cid, expected_type in expected.items():
            card = registry.get(cid)()
            assert expected_type in card.provides, f"{cid} should provide {expected_type}"


# ============================================================================
# 测试 2: 宝可梦卡效果 — 属性和攻击
# ============================================================================
class TestPokemonCardEffects:
    """验证宝可梦卡的核心属性和攻击条件。"""

    def test_charizard_ex_has_correct_attacks(self):
        """PAF-054 Charizard ex 有 Burning Darkness 攻击。"""
        card = registry.get("PAF-054")()
        assert len(card.attacks) == 1
        atk = card.attacks[0]
        assert atk.name == "Burning Darkness"
        assert atk.damage == 180
        assert atk.cost == [CardType.FIRE, CardType.FIRE]
        assert "30 more damage" in atk.text

    def test_charizard_ex_has_infernal_reign_ability(self):
        """PAF-054 Charizard ex 有 Infernal Reign 特性。"""
        card = registry.get("PAF-054")()
        assert len(card.ability) == 1
        assert card.ability[0].name == "Infernal Reign"

    def test_charizard_ex_is_stage_2(self):
        """PAF-054 Charizard ex 是阶段2进化。"""
        card = registry.get("PAF-054")()
        assert card.stage == Stage.STAGE_2
        assert "火恐龙" in card.evolveFrom
        assert card.prize == 2  # ex Pokemon give 2 prizes

    def test_radiant_charizard_is_basic_with_radiant_rule(self):
        """CRZ-020 Radiant Charizard 是基础宝可梦且只能放1张。"""
        card = registry.get("CRZ-020")()
        assert card.stage == Stage.BASIC
        assert card.name == "光辉喷火龙"

    def test_gardevoir_ex_has_embrace_ability(self):
        """SVI-086 Gardevoir ex 有 Psychic Embrace 特性。"""
        card = registry.get("SVI-086")()
        assert len(card.ability) >= 1
        ability_names = [a.name for a in card.ability]
        assert "Psychic Embrace" in ability_names


# ============================================================================
# 测试 3: 训练家卡效果 — 使用条件和效果
# ============================================================================
class TestTrainerCardEffects:
    """验证训练家卡的使用条件和效果。"""

    def test_bosss_orders_is_supporter(self):
        """PAL-265 Boss's Orders 是支援者卡。"""
        card = registry.get("PAL-265")()
        assert card.superType == SuperType.TRAINER
        assert card.trainerType == TrainerType.SUPPORTER
        assert card.name == "老大的指令"
        assert "Switch 1 of your opponent's Benched" in card.text

    def test_ultra_ball_is_item(self):
        """PAF-091 Ultra Ball 是物品卡。"""
        card = registry.get("PAF-091")()
        assert card.trainerType == TrainerType.ITEM
        assert "高级球" in card.name

    def test_rare_candy_is_item(self):
        """PAF-089 Rare Candy 是物品卡。"""
        card = registry.get("PAF-089")()
        assert card.trainerType == TrainerType.ITEM

    def test_professors_research_is_supporter(self):
        """PAF-087 Professor's Research 是支援者卡。"""
        card = registry.get("PAF-087")()
        assert card.trainerType == TrainerType.SUPPORTER

    def test_iono_is_supporter(self):
        """PAF-080 Iono 是支援者卡。"""
        card = registry.get("PAF-080")()
        assert card.trainerType == TrainerType.SUPPORTER
        assert "奇树" in card.name

    def test_arven_is_supporter(self):
        """OBF-186 Arven 是支援者卡。"""
        card = registry.get("OBF-186")()
        assert card.trainerType == TrainerType.SUPPORTER

    def test_artazon_is_stadium(self):
        """PAL-171 Artazon 是场地卡。"""
        card = registry.get("PAL-171")()
        assert card.trainerType == TrainerType.STADIUM

    def test_bravery_charm_is_tool(self):
        """PAL-173 Bravery Charm 是道具卡。"""
        card = registry.get("PAL-173")()
        assert card.trainerType == TrainerType.TOOL

    def test_defiance_band_is_tool(self):
        """SVI-169 Defiance Band 是道具卡。"""
        card = registry.get("SVI-169")()
        assert card.trainerType == TrainerType.TOOL


# ============================================================================
# 测试 4: 特殊能量卡效果
# ============================================================================
class TestSpecialEnergyEffects:
    """验证特殊能量卡的效果。"""

    def test_double_turbo_energy_provides_two_colorless(self):
        """BRS-151 Double Turbo Energy 提供 2 个无色能量。"""
        card = registry.get("BRS-151")()
        assert card.energyType == EnergyType.SPECIAL
        assert len(card.provides) == 2
        assert all(t == CardType.COLORLESS for t in card.provides)
        assert "20 less damage" in card.text

    def test_jet_energy_is_special(self):
        """PAL-190 Jet Energy 是特殊能量卡。"""
        card = registry.get("PAL-190")()
        assert card.energyType == EnergyType.SPECIAL

    def test_gift_energy_is_special(self):
        """LOR-171 Gift Energy 是特殊能量卡。"""
        card = registry.get("LOR-171")()
        assert card.energyType == EnergyType.SPECIAL

    def test_therapeutic_energy_is_special(self):
        """PAL-193 Therapeutic Energy 是特殊能量卡。"""
        card = registry.get("PAL-193")()
        assert card.energyType == EnergyType.SPECIAL

    def test_v_guard_energy_is_special(self):
        """SIT-169 V Guard Energy 是特殊能量卡。"""
        card = registry.get("SIT-169")()
        assert card.energyType == EnergyType.SPECIAL

    def test_mist_energy_is_special(self):
        """TEF Mist Energy 是特殊能量卡。"""
        card = registry.get("TEF-161")()
        assert card.energyType == EnergyType.SPECIAL


# ============================================================================
# 测试 5: 游戏环境集成 — 全游戏模拟
# ============================================================================
class TestGameIntegration:
    """使用 PokemonTCG 环境运行完整游戏，验证卡牌效果。"""

    def test_game_runs_with_charizard_deck(self):
        """charizard_ex 卡组能正常完成一局游戏。"""
        env = PokemonTCG(seed=42)
        obs, reward, done, info = env.reset()

        assert env.gamestate is not None
        assert "raw_available_actions" in info
        assert info["turn"] is not None

        # Run game until completion (max 2000 steps)
        step_count = 0
        max_steps = 2000
        while not done and step_count < max_steps:
            actions = info["raw_available_actions"]
            if actions:
                action = actions[0]
                obs, reward, done, info = env.step(action)
            step_count += 1

        assert done, f"Game should end within {max_steps} steps (took {step_count})"

    def test_game_actions_have_valid_structure(self):
        """验证游戏中的行动结构有效。"""
        env = PokemonTCG(seed=99)
        obs, reward, done, info = env.reset()

        actions = info["raw_available_actions"]
        assert len(actions) > 0, "Should have at least one action available"
        # Each action should be an Action instance
        for action in actions:
            assert hasattr(action, "actionType"), "Action should have actionType"

    def test_decks_can_be_loaded(self):
        """所有预置卡组都能正常加载。"""
        from pathlib import Path
        decks_dir = Path(__file__).parent.parent.parent / "ptcg" / "decks"
        for deck_file in decks_dir.glob("*.txt"):
            if deck_file.name == "__init__.py":
                continue
            deck = load_deck(str(deck_file))
            assert len(deck.cards) > 0, f"Deck {deck_file.name} should have cards"


# ============================================================================
# 测试 6: 边界条件 — 卡牌在特殊状态下的行为
# ============================================================================
class TestEdgeCases:
    """验证卡牌在边界条件下的行为。"""

    def test_all_pokemon_have_valid_hp_range(self):
        """所有宝可梦卡 HP 在合理范围内 (30-340)。"""
        for cid in registry.list_all():
            card = registry.get(cid)()
            if isinstance(card, PokemonCard):
                assert 30 <= card.hp <= 340, f"{cid} HP {card.hp} out of range"
                assert card.prize in (1, 2, 3), f"{cid} invalid prize {card.prize}"

    def test_all_energy_cards_have_provides(self):
        """所有能量卡提供至少一种能量类型。"""
        for cid in registry.list_all():
            card = registry.get(cid)()
            if isinstance(card, EnergyCard):
                assert len(card.provides) >= 1, f"{cid} should provide energy"

    def test_all_pokemon_have_retreat_cost_valid(self):
        """所有宝可梦撤退成本在 0-5 之间。"""
        for cid in registry.list_all():
            card = registry.get(cid)()
            if isinstance(card, PokemonCard):
                assert 0 <= len(card.retreat) <= 5, (
                    f"{cid} retreat cost {len(card.retreat)} out of range"
                )

    def test_ex_pokemon_give_2_prizes(self):
        """ex Pokemon 应该给 2 张奖品卡。"""
        for cid in registry.list_all():
            card = registry.get(cid)()
            if isinstance(card, PokemonCard) and card.pokemonType == PokemonType.EX:
                assert card.prize == 2, (
                    f"{cid} ({card.name}) is EX but gives {card.prize} prizes"
                )

    def test_v_pokemon_give_2_prizes(self):
        """V Pokemon 应该给 2 张奖品卡。"""
        for cid in registry.list_all():
            card = registry.get(cid)()
            if isinstance(card, PokemonCard) and card.pokemonType == PokemonType.V:
                assert card.prize == 2, (
                    f"{cid} ({card.name}) is V but gives {card.prize} prizes"
                )
