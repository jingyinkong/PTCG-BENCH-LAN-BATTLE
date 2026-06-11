from dataclasses import dataclass

import pytest

from ptcg.core.ops import (
    GameOp,
    InvalidOperationError,
    OpCategory,
    OperationResolver,
    OpType,
    PlayerSide,
    ResolverContext,
)


def _make_op() -> GameOp:
    return GameOp(type=OpType.MOVE_CARDS, category=OpCategory.STATE_OP, actor=PlayerSide.SELF)


@dataclass
class FakeAction:
    source: object | None = None


class FakeSourceWithoutResolve:
    pass


class FakeSourceSingleOp:
    def resolve_ops(self, ctx: ResolverContext) -> GameOp:
        return _make_op()


class FakeSourceListOps:
    def resolve_ops(self, ctx: ResolverContext) -> list[GameOp]:
        return [_make_op(), _make_op()]


class FakeSourceInvalidOps:
    def resolve_ops(self, ctx: ResolverContext) -> object:
        return {"invalid": True}


class FakeSourceNoReduceCall:
    def __init__(self) -> None:
        self.reduce_called = False

    def resolve_ops(self, ctx: ResolverContext) -> list[GameOp]:
        return [_make_op()]

    def reduce_action(self, action, state):
        self.reduce_called = True
        raise AssertionError("resolve_action 不应调用 reduce_action")


class FakeSourceCard:
    def resolve_effect_ops(self, ctx: ResolverContext, effect_name: str | None) -> list[GameOp]:
        assert effect_name == "on_play"
        return [_make_op()]


class FakeCardWithoutResolver:
    pass


def _make_ctx(action: object | None = None, source_card: object | None = None) -> ResolverContext:
    return ResolverContext(state=object(), action=action, source_card=source_card)


class TestOperationResolver:
    def test_resolve_action_returns_empty_when_source_has_no_resolve_ops(self):
        resolver = OperationResolver()
        ctx = _make_ctx(action=FakeAction(source=FakeSourceWithoutResolve()))

        assert resolver.resolve_action(ctx) == []

    def test_resolve_action_normalizes_single_game_op(self):
        resolver = OperationResolver()
        ctx = _make_ctx(action=FakeAction(source=FakeSourceSingleOp()))

        ops = resolver.resolve_action(ctx)

        assert len(ops) == 1
        assert isinstance(ops[0], GameOp)

    def test_resolve_action_returns_list_of_game_ops(self):
        resolver = OperationResolver()
        ctx = _make_ctx(action=FakeAction(source=FakeSourceListOps()))

        ops = resolver.resolve_action(ctx)

        assert len(ops) == 2
        assert all(isinstance(op, GameOp) for op in ops)

    def test_resolve_action_raises_on_invalid_return_type(self):
        resolver = OperationResolver()
        ctx = _make_ctx(action=FakeAction(source=FakeSourceInvalidOps()))

        with pytest.raises(InvalidOperationError):
            resolver.resolve_action(ctx)

    def test_resolve_action_raises_when_action_missing(self):
        resolver = OperationResolver()
        ctx = _make_ctx(action=None)

        with pytest.raises(InvalidOperationError):
            resolver.resolve_action(ctx)

    def test_resolve_action_does_not_call_reduce_action(self):
        resolver = OperationResolver()
        source = FakeSourceNoReduceCall()
        ctx = _make_ctx(action=FakeAction(source=source))

        ops = resolver.resolve_action(ctx)

        assert len(ops) == 1
        assert source.reduce_called is False

    def test_resolve_card_effect_returns_ops_when_source_card_supports_it(self):
        resolver = OperationResolver()
        ctx = _make_ctx(source_card=FakeSourceCard())

        ops = resolver.resolve_card_effect(ctx, effect_name="on_play")

        assert len(ops) == 1
        assert isinstance(ops[0], GameOp)

    def test_resolve_card_effect_returns_empty_when_source_card_has_no_resolver(self):
        resolver = OperationResolver()
        ctx = _make_ctx(source_card=FakeCardWithoutResolver())

        assert resolver.resolve_card_effect(ctx) == []

    def test_register_and_resolve_registered_calls_registered_function(self):
        resolver = OperationResolver()
        seen: list[ResolverContext] = []

        def custom_resolver(ctx: ResolverContext) -> list[GameOp]:
            seen.append(ctx)
            return [_make_op()]

        ctx = _make_ctx()
        resolver.register("custom", custom_resolver)

        ops = resolver.resolve_registered("custom", ctx)

        assert len(ops) == 1
        assert seen == [ctx]

    def test_resolve_registered_returns_empty_when_name_not_registered(self):
        resolver = OperationResolver()

        assert resolver.resolve_registered("missing", _make_ctx()) == []
