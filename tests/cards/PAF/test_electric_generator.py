"""Electric Generator (电气发生器) 测试 — PAF 079"""
import inspect

import pytest

from ptcg.core.card import ItemCard
from ptcg.core.enums import CardType
from ptcg.core.card_registry import registry


def make_card():
    """Get a fresh Electric Generator instance."""
    return registry.get("PAF-079")()


class TestElectricGeneratorIdentity:
    """卡牌基本属性验证（L1: Structure Check）。"""

    def test_name(self):
        card = make_card()
        assert card.name == "电气发生器"

    def test_set_and_number(self):
        card = make_card()
        assert card.set_name == "PAF"
        assert card.number == "079"
        assert card.id == "PAF-079"

    def test_card_type(self):
        card = make_card()
        assert isinstance(card, ItemCard)
        assert card.cardType == CardType.NONE

    def test_has_text(self):
        card = make_card()
        assert card.text
        assert len(card.text) > 10


class TestElectricGeneratorMethods:
    """卡牌接口验证（L2-L3: Action Generation & Handling）。"""

    def test_get_actions_exists(self):
        card = make_card()
        assert callable(getattr(card, "get_actions", None))

    def test_reduce_action_is_generator(self):
        card = make_card()
        assert callable(getattr(card, "reduce_action", None))
        assert inspect.isgeneratorfunction(card.reduce_action)
