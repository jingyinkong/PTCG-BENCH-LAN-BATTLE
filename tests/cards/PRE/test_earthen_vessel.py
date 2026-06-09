"""Earthen Vessel (大地容器) 测试 — PRE 106"""
import inspect
import pytest
from ptcg.core.card import ItemCard
from ptcg.core.enums import CardType
from ptcg.core.card_registry import registry

def make_card():
    return registry.get("PRE-106")()

class TestEarthenVesselIdentity:
    def test_name(self):
        assert make_card().name == "大地容器"
    def test_set_and_number(self):
        card = make_card()
        assert card.set_name == "PRE"
        assert card.number == "106"
        assert card.id == "PRE-106"
    def test_card_type(self):
        card = make_card()
        assert isinstance(card, ItemCard)
        assert card.cardType == CardType.NONE
    def test_has_text(self):
        card = make_card()
        assert card.text
        assert "弃" in card.text or "discard" in card.text.lower()

class TestEarthenVesselMethods:
    def test_get_actions_exists(self):
        assert callable(getattr(make_card(), "get_actions", None))
    def test_reduce_action_is_generator(self):
        card = make_card()
        assert callable(getattr(card, "reduce_action", None))
        assert inspect.isgeneratorfunction(card.reduce_action)
