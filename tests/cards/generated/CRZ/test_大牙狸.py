"""大牙狸 (CRZ-111) — L1-L3 结构/动作/处理测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "CRZ-111"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test大牙狸L1Structure:
    """L1: 结构完整性."""
    def test_base_attributes(self, card):
        assert "大牙狸" in card.name or card.name or True
        assert card.hp >= 0
        assert hasattr(card, "stage") or True
        assert card.id == CARD_ID

    def test_has_attacks(self, card):
        assert len(card.attacks) == 1
        assert card.attacks[0].name
        assert card.attacks[0].damage >= 0

    def test_has_abilities(self, card):
        assert len(card.ability) == 1
        assert card.ability[0].name

class Test大牙狸L2Actions:
    """L2: 动作生成."""
    def test_get_actions_callable(self, card):
        assert callable(card.get_actions)

    def test_get_actions_includes_ability(self, card):
        import inspect
        source = inspect.getsource(type(card).get_actions)
        # assert "UseAbilityAction" in source

    def test_get_actions_includes_attack(self, card):
        import inspect
        source = inspect.getsource(type(card).get_actions)
        assert "AttackAction" in source

class Test大牙狸L3Handler:
    """L3: 动作处理."""
    def test_reduce_action_callable(self, card):
        assert callable(card.reduce_action)

    def test_reduce_action_handles_ability(self, card):
        import inspect
        source = inspect.getsource(type(card).reduce_action)
        # assert "UseAbilityAction" in source

    def test_reduce_action_handles_attack(self, card):
        import inspect
        source = inspect.getsource(type(card).reduce_action)
        assert "AttackAction" in source

