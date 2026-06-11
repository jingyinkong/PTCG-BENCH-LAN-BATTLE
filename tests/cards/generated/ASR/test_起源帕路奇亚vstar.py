"""起源帕路奇亚VSTAR (ASR-040) — L1-L3 结构/动作/处理测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "ASR-040"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test起源帕路奇亚VSTARL1Structure:
    """L1: 结构完整性."""
    def test_base_attributes(self, card):
        assert card.name == "起源帕路奇亚VSTAR"
        assert getattr(card, 'hp', 0) == 280
        if hasattr(card, 'stage'):
            assert str(card.stage) == 'Stage.BASIC'
        assert card.id == CARD_ID

    def test_has_attacks(self, card):
        if hasattr(card, 'attacks'):
            assert len(card.attacks) == 1
            assert card.attacks[0].name == "亚空潮漩"
            assert card.attacks[0].damage == 60

    def test_has_abilities(self, card):
        if hasattr(card, 'ability'):
            assert len(card.ability) == 1
            assert card.ability[0].name == "星耀空扉"

class Test起源帕路奇亚VSTARL2Actions:
    """L2: 动作生成."""
    def test_get_actions_callable(self, card):
        assert callable(card.get_actions)

    def test_get_actions_includes_attack(self, card):
        import inspect
        source = inspect.getsource(type(card).get_actions)
        assert "AttackAction" in source

class Test起源帕路奇亚VSTARL3Handler:
    """L3: 动作处理."""
    def test_reduce_action_callable(self, card):
        assert callable(card.reduce_action)

    def test_reduce_action_handles_attack(self, card):
        import inspect
        source = inspect.getsource(type(card).reduce_action)
        assert "AttackAction" in source

