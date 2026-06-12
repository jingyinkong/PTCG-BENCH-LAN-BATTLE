from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ptcg.core.ops.context import ExecutionContext, ResolverContext
from ptcg.core.ops.errors import InvalidOperationError
from ptcg.core.ops.executor import OperationExecutor
from ptcg.core.ops.resolver import OperationResolver
from ptcg.core.ops.types import GameOp, OpResult, OpType


@dataclass
class BridgeResult:
    used_semantic: bool
    fallback_required: bool
    op_results: list[Any] = field(default_factory=list)
    events: list[Any] = field(default_factory=list)
    reason: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)


class SemanticReducerBridge:
    """旁路语义桥接器，只在测试或未来显式桥接场景中使用。"""

    _SUPPORTED_OP_TYPES = {
        OpType.MOVE_CARDS,
        OpType.DRAW_CARDS,
        OpType.DISCARD_CARDS,
    }

    def __init__(self, resolver: OperationResolver | None = None, executor: OperationExecutor | None = None):
        self.resolver = resolver or OperationResolver()
        self.executor = executor or OperationExecutor()

    def reduce(self, action: Any, state: Any) -> BridgeResult:
        if action is None:
            raise InvalidOperationError("SemanticReducerBridge.reduce 需要有效 action。")

        source = getattr(action, "source", None)
        payload = self._build_payload(action)

        if not hasattr(source, "resolve_ops"):
            return BridgeResult(
                used_semantic=False,
                fallback_required=True,
                reason="source_has_no_resolve_ops",
                payload=payload,
            )

        ops = self.try_resolve_ops(action, state)
        if len(ops) == 0:
            return BridgeResult(
                used_semantic=False,
                fallback_required=True,
                reason="resolver_returned_empty",
                payload=payload,
            )

        self._validate_semantic_ops(ops)
        op_results = self.execute_semantic_ops(action, state, ops)
        events = [event for result in op_results for event in result.events]

        semantic_payload = dict(payload)
        semantic_payload["op_count"] = len(ops)
        return BridgeResult(
            used_semantic=True,
            fallback_required=False,
            op_results=op_results,
            events=events,
            reason="semantic_ops_executed",
            payload=semantic_payload,
        )

    def try_resolve_ops(self, action: Any, state: Any) -> list[GameOp]:
        resolver_ctx = self._build_resolver_context(action, state)
        return self.resolver.resolve_action(resolver_ctx)

    def execute_semantic_ops(self, action: Any, state: Any, ops: list[GameOp]) -> list[OpResult]:
        self._validate_semantic_ops(ops)
        execution_ctx = self._build_execution_context(action, state)
        return self.executor.execute_ops(execution_ctx, ops)

    @staticmethod
    def should_fallback_to_legacy(result: BridgeResult) -> bool:
        return result.fallback_required

    def _validate_semantic_ops(self, ops: list[GameOp]) -> None:
        for op in ops:
            if not isinstance(op, GameOp):
                raise InvalidOperationError("SemanticReducerBridge 只接受 GameOp 列表。")
            if op.type not in self._SUPPORTED_OP_TYPES:
                raise InvalidOperationError(f"SemanticReducerBridge 当前不支持 op: {op.type.value}")

    def _build_resolver_context(self, action: Any, state: Any) -> ResolverContext:
        acting_player, opponent_player = self._resolve_players(action, state)
        return ResolverContext(
            state=state,
            action=action,
            acting_player=acting_player,
            opponent_player=opponent_player,
            source_card=getattr(action, "source", None),
            target_card=getattr(action, "target", None),
            metadata=self._build_metadata(action),
        )

    def _build_execution_context(self, action: Any, state: Any) -> ExecutionContext:
        acting_player, opponent_player = self._resolve_players(action, state)
        return ExecutionContext(
            state=state,
            action=action,
            acting_player=acting_player,
            opponent_player=opponent_player,
            source_card=getattr(action, "source", None),
            metadata=self._build_metadata(action),
        )

    @staticmethod
    def _build_metadata(action: Any) -> dict[str, Any]:
        source = getattr(action, "source", None)
        return {
            "bridge_mode": "semantic_fallback",
            "allow_generator": False,
            "allow_choice": False,
            "action_type": type(action).__name__,
            "source_type": type(source).__name__ if source is not None else None,
        }

    def _build_payload(self, action: Any) -> dict[str, Any]:
        payload = self._build_metadata(action)
        payload["op_count"] = 0
        return payload

    @staticmethod
    def _resolve_players(action: Any, state: Any) -> tuple[Any | None, Any | None]:
        if action is None or state is None or not hasattr(action, "playerId"):
            return None, None
        if not hasattr(state, "player1") or not hasattr(state, "player2"):
            return None, None

        player_id = getattr(action, "playerId")
        player1 = getattr(state, "player1")
        player2 = getattr(state, "player2")

        if getattr(player1, "id", None) == player_id:
            return player1, player2
        if getattr(player2, "id", None) == player_id:
            return player2, player1
        return None, None
