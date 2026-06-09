"""BRS 卡包 Tier 3 卡牌测试 — 5 张 V."""
import pytest
from ptcg.core.card_registry import registry
from ptcg.core.enums import SuperType, Stage, CardType

CARDS = [
    ("BRS-022", "炎帝V", 230, Stage.BASIC, CardType.FIRE),
    ("BRS-040", "霓虹鱼V", 170, Stage.BASIC, CardType.WATER),
    ("BRS-045", "雷丘V", 200, Stage.BASIC, CardType.LIGHTNING),
    ("BRS-048", "雷公V", 200, Stage.BASIC, CardType.LIGHTNING),
    
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
