"""洛托姆V LOR-058 测试 — Tier 3 L1-L3."""
import pytest
from ptcg.core.card_registry import registry
from ptcg.core.enums import SuperType, Stage, CardType
from ptcg.core.ability import ActiveAbility

CARD_ID = "LOR-058"


@pytest.fixture
def card():
    return registry.get(CARD_ID)()


class TestL1Structure:
    def test_base_attributes(self, card):
        assert card.name == "洛托姆V"
        assert card.hp == 190
        assert card.stage == Stage.BASIC
        assert card.superType == SuperType.POKEMON
        assert card.cardType == CardType.LIGHTNING

    def test_has_ability(self, card):
        assert len(card.ability) > 0, "洛托姆V应有Instant Charge特性"

    def test_ability_is_active(self, card):
        assert any(isinstance(ab, ActiveAbility) for ab in card.ability), \
            "Instant Charge应为ActiveAbility"

    def test_has_attacks(self, card):
        assert len(card.attacks) >= 1
        atk = card.attacks[0]
        assert atk.name == "废品短路"
        assert atk.damage == 40

    def test_has_prize_2(self, card):
        assert card.prize == 2, "V卡应给2奖品"


class TestL2Actions:
    def test_get_actions_not_empty(self, card):
        """验证get_actions被正确覆盖（非空实现）."""
        import inspect
        source = inspect.getsource(type(card).get_actions)
        assert "UseAbilityAction" in source, "get_actions应生成UseAbilityAction"
        assert "AttackAction" in source, "get_actions应生成AttackAction"


class TestL3Handler:
    def test_reduce_action_handles_ability(self, card):
        """验证reduce_action处理UseAbilityAction."""
        import inspect
        source = inspect.getsource(type(card).reduce_action)
        assert "UseAbilityAction" in source, "reduce_action应处理UseAbilityAction"
        assert "AttackAction" in source, "reduce_action应处理AttackAction"
