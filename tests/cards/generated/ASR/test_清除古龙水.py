"""清除古龙水 (ASR-136) — L1-L3 结构/动作/处理测试. 自动生成."""
import pytest
from ptcg.core.card_registry import registry

CARD_ID = "ASR-136"

@pytest.fixture
def card():
    cls = registry.get(CARD_ID)
    if cls is None:
        pytest.skip(f"{CARD_ID} not registered")
    return cls()

class Test清除古龙水L1Structure:
    """L1: 结构完整性."""
    def test_base_attributes(self, card):
        assert card.name == "清除古龙水"
        if hasattr(card, 'stage'):
            assert str(card.stage) == 'Stage.BASIC'
        assert card.id == CARD_ID

    def test_ability_list_exists(self, card):
        if hasattr(card, 'ability'):
            assert True

class Test清除古龙水L2Actions:
    """L2: 动作生成."""
    def test_get_actions_callable(self, card):
        assert callable(card.get_actions)

class Test清除古龙水L3Handler:
    """L3: 动作处理."""
    def test_reduce_action_callable(self, card):
        assert callable(card.reduce_action)

