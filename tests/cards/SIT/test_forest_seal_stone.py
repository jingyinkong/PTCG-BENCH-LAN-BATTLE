"""Forest Seal Stone (森林封印石) 测试 — SIT 156"""
import inspect
import pytest
from ptcg.core.card import ToolCard
from ptcg.core.enums import CardType
from ptcg.core.card_registry import registry

def make_card():
    return registry.get("SIT-156")()

class TestForestSealStoneIdentity:
    def test_name(self):
        assert make_card().name == "森林封印石"
    def test_set_and_number(self):
        card = make_card()
        assert card.set_name == "SIT"
        assert card.number == "156"
        assert card.id == "SIT-156"
    def test_card_type(self):
        card = make_card()
        assert isinstance(card, ToolCard)
        assert card.cardType == CardType.NONE
    def test_has_ability(self):
        card = make_card()
        assert hasattr(card, "ability")
        assert card.ability
        assert len(card.ability) == 1
        assert card.ability[0].name == "Star Alchemy"
    def test_has_text(self):
        card = make_card()
        assert card.text

class TestForestSealStoneMethods:
    def test_get_actions_exists(self):
        assert callable(getattr(make_card(), "get_actions", None))
    def test_reduce_action_is_generator(self):
        card = make_card()
        assert callable(getattr(card, "reduce_action", None))
        assert inspect.isgeneratorfunction(card.reduce_action)
    def test_initial_state_not_attached(self):
        card = make_card()
        assert card.hasAttached is False
        assert card.attachedTo is None
