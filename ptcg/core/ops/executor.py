from __future__ import annotations

from ptcg.core.ops.context import ExecutionContext
from ptcg.core.ops.errors import InvalidOperationError
from ptcg.core.ops.events import EventSink, EventVisibility, OperationEvent, OperationEventType
from ptcg.core.ops.types import GameOp, OpResult, OpType, ZoneName, ZoneRef
from ptcg.core.ops.zones import ZoneService


class OperationExecutor:
    """旁路语义执行器，供后续迁移与测试使用。"""

    def __init__(self, zone_service: ZoneService | None = None, event_sink: EventSink | None = None):
        self.zone_service = zone_service or ZoneService()
        self.event_sink = event_sink or EventSink()

    def execute_op(self, ctx: ExecutionContext, op: GameOp) -> OpResult:
        if op.type == OpType.MARK_SUPPORTER_PLAYED:
            result = self._execute_mark_supporter_played(ctx, op)
        elif op.type == OpType.MOVE_CARDS:
            result = self._execute_move_cards(ctx, op)
        elif op.type == OpType.DRAW_CARDS:
            result = self._execute_draw_cards(ctx, op)
        elif op.type == OpType.DISCARD_CARDS:
            result = self._execute_discard_cards(ctx, op)
        else:
            raise InvalidOperationError(f"OperationExecutor 暂不支持 op: {op.type.value}")

        for event in result.events:
            self.event_sink.emit(event)
        return result

    def execute_ops(self, ctx: ExecutionContext, ops: list[GameOp]) -> list[OpResult]:
        results: list[OpResult] = []
        for op in sorted(ops, key=lambda item: item.order):
            results.append(self.execute_op(ctx, op))
        return results

    def _execute_move_cards(self, ctx: ExecutionContext, op: GameOp) -> OpResult:
        source = self._require_zone_ref(op.source, "move_cards.source")
        target = self._require_zone_ref(op.target, "move_cards.target")
        if "cards" not in op.params:
            raise InvalidOperationError("move_cards 需要在 params 中提供 cards。")

        event = self.zone_service.move_cards(
            ctx=ctx,
            cards=op.params["cards"],
            source=source,
            target=target,
            public=op.public,
        )
        event.op_type = op.type.value
        event.actor = op.actor.value
        return OpResult(op=op, success=True, events=[event])

    def _execute_mark_supporter_played(self, ctx: ExecutionContext, op: GameOp) -> OpResult:
        if op.actor.value != "self":
            raise InvalidOperationError("mark_supporter_played 只允许作用于当前玩家。")
        if ctx.acting_player is None:
            raise InvalidOperationError("mark_supporter_played 需要 ExecutionContext.acting_player。")

        ctx.acting_player.supporterPlayedTurn = True
        event = OperationEvent(
            event_type=OperationEventType.SUPPORTER_PLAYED_MARKED,
            op_type=op.type.value,
            actor=op.actor.value,
            visibility=EventVisibility.PUBLIC,
            payload={"field": "supporterPlayedTurn", "value": True},
        )
        return OpResult(op=op, success=True, events=[event])

    def _execute_draw_cards(self, ctx: ExecutionContext, op: GameOp) -> OpResult:
        count = op.params.get("count")
        if not isinstance(count, int):
            raise InvalidOperationError("draw_cards 需要整数 count。")

        source = self._coerce_zone_ref(op.source, ZoneRef(side=op.actor, zone=ZoneName.LEFT), "draw_cards.source")
        target = self._coerce_zone_ref(op.target, ZoneRef(side=op.actor, zone=ZoneName.HAND), "draw_cards.target")

        source_zone = self.zone_service.resolve_zone(ctx, source)
        actual_count = min(count, len(source_zone))
        cards = list(source_zone[:actual_count])

        event = self.zone_service.move_cards(
            ctx=ctx,
            cards=cards,
            source=source,
            target=target,
            public=op.public,
        )
        event.op_type = op.type.value
        event.actor = op.actor.value
        return OpResult(
            op=op,
            success=True,
            events=[event],
            payload={"requested_count": count, "actual_count": actual_count},
        )

    def _execute_discard_cards(self, ctx: ExecutionContext, op: GameOp) -> OpResult:
        source = self._coerce_zone_ref(op.source, ZoneRef(side=op.actor, zone=ZoneName.HAND), "discard_cards.source")
        target = self._coerce_zone_ref(
            op.target,
            ZoneRef(side=op.actor, zone=ZoneName.DISCARD),
            "discard_cards.target",
        )

        source_zone = self.zone_service.resolve_zone(ctx, source)
        cards = op.params.get("cards")
        count = op.params.get("count")

        if cards is not None:
            cards_to_move = cards
        elif count == "all":
            cards_to_move = list(source_zone)
        elif isinstance(count, int):
            raise InvalidOperationError("discard_cards 的 count=N 需要选择语义，第一版暂不支持。")
        else:
            raise InvalidOperationError("discard_cards 需要提供 cards 或 count='all'。")

        event = self.zone_service.move_cards(
            ctx=ctx,
            cards=cards_to_move,
            source=source,
            target=target,
            public=op.public,
        )
        event.op_type = op.type.value
        event.actor = op.actor.value
        return OpResult(op=op, success=True, events=[event])

    @staticmethod
    def _require_zone_ref(value: object, field_name: str) -> ZoneRef:
        if not isinstance(value, ZoneRef):
            raise InvalidOperationError(f"{field_name} 必须是 ZoneRef。")
        return value

    @staticmethod
    def _coerce_zone_ref(value: object | None, default: ZoneRef, field_name: str) -> ZoneRef:
        if value is None:
            return default
        if not isinstance(value, ZoneRef):
            raise InvalidOperationError(f"{field_name} 必须是 ZoneRef。")
        return value
