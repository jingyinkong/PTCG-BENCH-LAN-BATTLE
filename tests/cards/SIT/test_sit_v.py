"""SIT 卡包 Tier 3 卡牌测试 — 4 张 V/VSTAR."""
import pytest
from ptcg.core.card_registry import registry
from ptcg.core.enums import SuperType, Stage, CardType

CARDS = [
    ("SIT-135", "雷吉铎拉戈V", 220, Stage.BASIC, CardType.DRAGON),
    ("SIT-136", "雷吉铎拉戈VSTAR", 280, Stage.VSTAR, CardType.DRAGON),
    ("SIT-138", "洛奇亚V", 220, Stage.BASIC, CardType.COLORLESS),
    ("SIT-139", "洛奇亚VSTAR", 280, Stage.VSTAR, CardType.COLORLESS),
]


@pytest.mark.parametrize("cid,name,hp,stage,ctype", CARDS)
def test_base_attrs(cid, name, hp, stage, ctype):
    card = registry.get(cid)()
    assert card.name == name
    assert card.hp == hp
    assert card.stage == stage
    assert card.superType == SuperType.POKEMON
    assert card.cardType == ctype
    assert card.prize >= 2
    assert len(card.attacks) >= 1


@pytest.mark.parametrize("cid,name,hp,stage,ctype", CARDS)
def test_generates_attack(cid, name, hp, stage, ctype):
    import inspect
    card = registry.get(cid)()
    source = inspect.getsource(type(card).get_actions)
    assert "AttackAction" in source, f"{name}: 应生成AttackAction"
