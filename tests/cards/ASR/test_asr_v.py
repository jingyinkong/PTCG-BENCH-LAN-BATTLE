"""ASR 卡包 Tier 3 卡牌测试 — 6 张 V/VSTAR."""
import pytest
from ptcg.core.card_registry import registry
from ptcg.core.enums import SuperType, Stage, CardType

CARDS = [
    ("ASR-039", "起源帕路奇亚V", 220, Stage.BASIC, CardType.WATER),
    ("ASR-040", "起源帕路奇亚VSTAR", 280, Stage.BASIC, CardType.WATER),
    ("ASR-113", "起源帝牙卢卡V", 220, Stage.BASIC, CardType.METAL),
    ("ASR-114", "起源帝牙卢卡VSTAR", 280, Stage.BASIC, CardType.METAL),
    ("ASR-133", "智挥猩V", 210, Stage.BASIC, CardType.COLORLESS),
    ("ASR-134", "诡角鹿V", 220, Stage.BASIC, CardType.COLORLESS),
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
