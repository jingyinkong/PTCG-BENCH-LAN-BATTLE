from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable


class EventVisibility(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    HIDDEN = "hidden"


class OperationEventType(str, Enum):
    SUPPORTER_PLAYED_MARKED = "supporter_played_marked"
    CARDS_MOVED = "cards_moved"
    DAMAGE_APPLIED = "damage_applied"
    HP_HEALED = "hp_healed"
    ENERGY_ATTACHED = "energy_attached"
    ENERGY_DISCARDED = "energy_discarded"
    DECK_SHUFFLED = "deck_shuffled"
    CONDITION_APPLIED = "condition_applied"
    CHOICE_REQUESTED = "choice_requested"
    PRIZE_TAKEN = "prize_taken"
    POKEMON_KNOCKED_OUT = "pokemon_knocked_out"
    TURN_ENDED = "turn_ended"


@dataclass
class OperationEvent:
    event_type: OperationEventType
    op_type: str | None = None
    actor: str | None = None
    source: str | None = None
    target: str | None = None
    card_ids: list[str] = field(default_factory=list)
    count: int | None = None
    visibility: EventVisibility = EventVisibility.PUBLIC
    message: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class EventSink:
    """简单的事件收集器，为未来桥接现有事件系统预留接口。"""

    _events: list[OperationEvent] = field(default_factory=list)

    def emit(self, event: OperationEvent) -> None:
        self._events.append(event)

    def extend(self, events: Iterable[OperationEvent]) -> None:
        self._events.extend(events)

    def clear(self) -> None:
        self._events.clear()

    def list_events(self) -> list[OperationEvent]:
        return list(self._events)
