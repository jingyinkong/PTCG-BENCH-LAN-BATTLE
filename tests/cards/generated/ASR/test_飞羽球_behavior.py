"""飞羽球 (ASR-141) — L4 效果行为测试. 自动生成."""
import pytest
from ptcg.core.action import AttackAction
from ptcg.core.card_registry import registry
from ptcg.core.enums import CardPosition, CardType, PokemonPosition

CARD_ID = "ASR-141"


def _make_card():
    return registry.get(CARD_ID)()


def _make_opponent():
    opp = registry.get("ASR-133")()
    opp.position = PokemonPosition.ACTIVE
    opp.cardPosition = CardPosition.ACTIVE
    opp.index = 0
    if not hasattr(opp, "max_hp"):
        opp.max_hp = opp.hp
    return opp


class Test飞羽球L4Behavior:
    """L4: 效果行为验证（snapshot_game 预设状态+状态断言）."""
