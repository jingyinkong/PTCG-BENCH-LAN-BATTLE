from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class OpPriority(str, Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"


class OpCategory(str, Enum):
    STATE_OP = "state_op"
    CHOICE_OP = "choice_op"
    FLOW_OP = "flow_op"


class OpType(str, Enum):
    MARK_SUPPORTER_PLAYED = "mark_supporter_played"
    MOVE_CARDS = "move_cards"
    DRAW_CARDS = "draw_cards"
    DISCARD_CARDS = "discard_cards"
    PLAY_POKEMON = "play_pokemon"
    EVOLVE_POKEMON = "evolve_pokemon"
    ATTACH_ENERGY = "attach_energy"
    DEAL_DAMAGE = "deal_damage"
    APPLY_SPECIAL_CONDITION = "apply_special_condition"
    END_TURN = "end_turn"
    CHOOSE_CARDS = "choose_cards"
    SEARCH_DECK = "search_deck"
    SWITCH_ACTIVE = "switch_active"
    TAKE_PRIZE = "take_prize"
    RECOVER_ENERGY = "recover_energy"
    HEAL = "heal"
    KNOCKOUT = "knockout"
    COIN_FLIP = "coin_flip"
    STADIUM_LIFECYCLE = "stadium_lifecycle"
    ON_KNOCKED_OUT_TOOL = "on_knocked_out_tool"
    LOST_ZONE = "lost_zone"
    RECURSIVE_DELEGATION = "recursive_delegation"


class ZoneName(str, Enum):
    HAND = "hand"
    DECK = "deck"
    LEFT = "left"
    DISCARD = "discard"
    PRIZE = "prize"
    ACTIVE = "active"
    BENCH = "bench"
    ATTACHMENT = "attachment"
    STADIUM = "stadium"
    LOST_ZONE = "lost_zone"


class PlayerSide(str, Enum):
    SELF = "self"
    OPPONENT = "opponent"


@dataclass(frozen=True)
class ZoneRef:
    side: PlayerSide
    zone: ZoneName
    index: int | None = None
    owner_id: str | None = None


@dataclass(frozen=True)
class TargetRef:
    side: PlayerSide
    zone: ZoneName | None = None
    index: int | None = None
    card_id: str | None = None
    runtime_id: str | None = None


@dataclass
class GameOp:
    type: OpType
    category: OpCategory
    actor: PlayerSide
    order: int = 0
    source: ZoneRef | None = None
    target: ZoneRef | TargetRef | None = None
    params: dict[str, Any] = field(default_factory=dict)
    optional: bool = False
    public: bool = False
    reveal: bool = False
    requires_choice: bool = False
    condition: dict[str, Any] | None = None
    priority: OpPriority | None = None


@dataclass
class OpResult:
    op: GameOp
    success: bool
    events: list[Any] = field(default_factory=list)
    message: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
