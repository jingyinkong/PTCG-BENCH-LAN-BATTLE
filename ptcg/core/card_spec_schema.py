"""PTCG 卡牌声明式 JSON Schema — Pydantic 模型。

定义 CardSpec 格式，与 effect_primitives.py 的 18 个原语配套。
"""
from typing import Literal, Optional
from pydantic import BaseModel, field_validator


class PrimitiveCall(BaseModel):
    """单个原语调用。op = PRIMITIVE_REGISTRY key, params = kwargs."""
    op: str
    params: dict = {}


class EffectStep(BaseModel):
    """效果步骤 — 触发条件 + 原语序列。"""
    trigger: Literal["on_play", "on_attack", "on_ability"] = "on_play"
    primitives: list[PrimitiveCall] = []
    condition: Optional[str] = None


class AttackDef(BaseModel):
    name: str
    damage: int = 0
    cost: list[str] = []
    text: str = ""


class AbilityDef(BaseModel):
    name: str
    type: str = ""
    text: str = ""


class CardSpec(BaseModel):
    """卡牌声明式描述。"""
    card_id: str
    name: str
    set_name: str = ""
    number: str = ""
    super_type: Literal["POKEMON", "TRAINER", "ENERGY"] = "POKEMON"

    # Pokemon
    hp: Optional[int] = None
    stage: str = ""
    pokemon_type: str = ""
    card_type: str = ""
    retreat: list[str] = []
    weakness: list[str] = []
    resistance: list[str] = []
    prize: int = 1
    attacks: list[AttackDef] = []
    abilities: list[AbilityDef] = []

    # Trainer
    trainer_type: Optional[Literal["ITEM", "SUPPORTER", "STADIUM", "TOOL"]] = None
    effect_text: str = ""

    # Energy
    energy_type: str = ""
    provides: list[str] = []

    # Effects
    effects: list[EffectStep] = []
    conditions: list[str] = []
