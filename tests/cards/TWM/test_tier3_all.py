"""剩余 Tier 3 卡牌批量测试."""
import pytest
from ptcg.core.card_registry import registry
from ptcg.core.enums import SuperType, Stage, CardType

CARDS = [
    ("TWM-025", "厄诡椪 碧草面具ex", 210, Stage.BASIC, CardType.GRASS),
    ("TWM-141", "月月熊 赫月ex", 260, Stage.BASIC, CardType.COLORLESS),
    ("TEF-123", "猛雷鼓ex", 240, Stage.BASIC, CardType.DRAGON),
    ("TEF-129", "土龙节节", 140, Stage.STAGE_1, CardType.COLORLESS),
    ("SFA-038", "吉雉鸡ex", 210, Stage.BASIC, CardType.DARK),
    ("SFA-039", "桃歹郎ex", 190, Stage.BASIC, CardType.DARK),
    ("SCR-128", "太乐巴戈斯ex", 230, Stage.BASIC, CardType.COLORLESS),
    ("SSP-076", "拉帝亚斯ex", 210, Stage.BASIC, CardType.PSYCHIC),
    ("SSP-130", "铝钢桥龙ex", 300, Stage.STAGE_1, CardType.METAL),
    ("SP-294", "洗翠 顽皮雷弹V", 210, Stage.BASIC, CardType.GRASS),
    ("MEW-151", "梦幻ex", 180, Stage.BASIC, CardType.PSYCHIC),
    ("ASC-057", "皮卡丘ex", 200, Stage.BASIC, CardType.LIGHTNING),
    ("PAR-139", "赛富豪ex", 260, Stage.STAGE_1, CardType.METAL),
    ("PRE-031", "铁臂膀ex", 230, Stage.BASIC, CardType.LIGHTNING),
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
