from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ptcg.core.ops.context import ResolverContext
from ptcg.core.ops.errors import InvalidOperationError
from ptcg.core.ops.types import GameOp


ResolverFunc = Callable[[ResolverContext], list[GameOp] | GameOp | None]


class OperationResolver:
    """旁路 resolver，只负责把 Action/Card effect 归一化为 GameOp 列表。"""

    def __init__(self, registry: dict[Any, ResolverFunc] | None = None):
        self.registry: dict[Any, ResolverFunc] = dict(registry or {})

    def resolve_action(self, ctx: ResolverContext) -> list[GameOp]:
        if ctx.action is None:
            raise InvalidOperationError("ResolverContext.action 不能为空。")

        source = getattr(ctx.action, "source", None)
        resolve_ops = getattr(source, "resolve_ops", None)
        if resolve_ops is None:
            return []

        return self._normalize_ops(resolve_ops(ctx))

    def resolve_card_effect(self, ctx: ResolverContext, effect_name: str | None = None) -> list[GameOp]:
        source_card = ctx.source_card
        resolve_effect_ops = getattr(source_card, "resolve_effect_ops", None)
        if resolve_effect_ops is None:
            return []

        return self._normalize_ops(resolve_effect_ops(ctx, effect_name))

    def register(self, action_type_or_name: Any, resolver_func: ResolverFunc) -> None:
        self.registry[action_type_or_name] = resolver_func

    def resolve_registered(self, name: Any, ctx: ResolverContext) -> list[GameOp]:
        resolver_func = self.registry.get(name)
        if resolver_func is None:
            return []
        return self._normalize_ops(resolver_func(ctx))

    def _normalize_ops(self, raw_ops: list[GameOp] | GameOp | None) -> list[GameOp]:
        if raw_ops is None:
            return []
        if isinstance(raw_ops, GameOp):
            return [raw_ops]
        if isinstance(raw_ops, list):
            self._validate_ops(raw_ops)
            return raw_ops
        raise InvalidOperationError("resolver 必须返回 GameOp、list[GameOp] 或 None。")

    @staticmethod
    def _validate_ops(ops: list[GameOp]) -> None:
        for op in ops:
            if not isinstance(op, GameOp):
                raise InvalidOperationError("resolver 返回的列表中存在非 GameOp 元素。")
