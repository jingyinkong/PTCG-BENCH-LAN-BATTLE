"""effect_primitives.py 单元测试."""
import pytest
from ptcg.core.effect_primitives import (
    apply_weakness_resistance, deal_damage, heal,
    flip_coin, PRIMITIVE_COUNT, PRIMITIVE_REGISTRY,
)
from ptcg.core.enums import CardType, Coin
from ptcg.core.card_registry import registry


def _make_pokemon(card_id="ASR-133"):
    """创建真实的宝可梦卡实例用于测试。"""
    cls = registry.get(card_id)
    return cls()


class TestWeaknessResistance:
    def test_weakness_doubles(self):
        source = _make_pokemon("ASR-133")  # 智挥猩V - PSYCHIC type
        source.cardType = CardType.PSYCHIC
        target = _make_pokemon("ASR-133")
        target.weakness = [CardType.PSYCHIC]
        target.resistance = []
        assert apply_weakness_resistance(source, target, 50) == 100

    def test_neutral(self):
        source = _make_pokemon("ASR-133")
        source.cardType = CardType.WATER
        target = _make_pokemon("ASR-133")
        target.weakness = [CardType.FIRE]
        target.resistance = []
        assert apply_weakness_resistance(source, target, 50) == 50


class TestDamage:
    def test_no_ko(self):
        target = _make_pokemon("ASR-133")
        target.hp = 100
        assert deal_damage(target, 30) is False
        assert target.hp == 70

    def test_ko(self):
        target = _make_pokemon("ASR-133")
        target.hp = 20
        assert deal_damage(target, 30) is True


class TestHeal:
    def test_normal(self):
        target = _make_pokemon("ASR-133")
        target.hp = 50
        target.max_hp = 100
        assert heal(target, 30) == 30
        assert target.hp == 80


class TestCoin:
    def test_valid(self):
        for _ in range(10):
            assert flip_coin() in (Coin.HEAD, Coin.TAIL)


class TestRegistry:
    def test_count(self):
        assert 16 <= PRIMITIVE_COUNT <= 25, f"Got {PRIMITIVE_COUNT}"

    def test_docstrings(self):
        for name, fn in PRIMITIVE_REGISTRY.items():
            assert callable(fn), f"{name} not callable"
            assert fn.__doc__, f"{name} missing docstring"
