"""OBF 卡包 Tier 3 卡牌测试."""
import pytest
from ptcg.core.card_registry import registry
from ptcg.core.enums import SuperType, Stage, CardType

CARDS = [
    ("OBF-125", "喷火龙ex", 330, Stage.STAGE_2, CardType.DARK),
    ("OBF-164", "大比鸟ex", 280, Stage.STAGE_2, CardType.COLORLESS),
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
