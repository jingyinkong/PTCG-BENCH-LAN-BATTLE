"""LOR 卡包剩余 Tier 3 测试 — 2 张 VSTAR."""
import pytest
from ptcg.core.card_registry import registry
from ptcg.core.enums import SuperType, Stage, CardType

CARDS = [
    ("LOR-131", "骑拉帝纳VSTAR", 280, Stage.VSTAR, CardType.DRAGON),
    ("LOR-136", "洗翠 黏美龙VSTAR", 270, Stage.BASIC, CardType.DRAGON),
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


@pytest.mark.parametrize("cid,name,hp,stage,ctype", CARDS)
def test_generates_attack(cid, name, hp, stage, ctype):
    import inspect
    card = registry.get(cid)()
    source = inspect.getsource(type(card).get_actions)
    assert "AttackAction" in source, f"{name}: 应生成AttackAction"
