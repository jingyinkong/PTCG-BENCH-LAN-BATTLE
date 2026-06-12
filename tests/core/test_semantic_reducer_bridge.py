from dataclasses import dataclass, field

import pytest

from ptcg.core.enums import CardPosition, PlayerId, PokemonPosition
from ptcg.core.ops import (
    BridgeResult,
    InvalidOperationError,
    OpCategory,
    OperationEventType,
    OpType,
    PlayerSide,
    SemanticReducerBridge,
    ZoneName,
    ZoneRef,
)
from ptcg.core.ops.context import ResolverContext


@dataclass
class FakeCard:
    id: str
    name: str
    cardPosition: CardPosition
    index: int = 0


@dataclass
class FakePokemon(FakeCard):
    position: PokemonPosition = PokemonPosition.BENCH
    attachment: list[FakeCard] = field(default_factory=list)


@dataclass
class FakePlayer:
    id: PlayerId
    hand: list[FakeCard] = field(default_factory=list)
    left: list[FakeCard] = field(default_factory=list)
    deck: list[FakeCard] = field(default_factory=list)
    discard: list[FakeCard] = field(default_factory=list)
    prize: list[FakeCard] = field(default_factory=list)
    bench: list[FakePokemon] = field(default_factory=list)
    active: list[FakePokemon] = field(default_factory=list)
    lostZone: list[FakeCard] = field(default_factory=list)


@dataclass
class FakeState:
    player1: FakePlayer
    player2: FakePlayer
    stadium: list[FakeCard] = field(default_factory=list)
    auto_events: list[str] = field(default_factory=list)


@dataclass
class FakeAction:
    source: object | None
    playerId: PlayerId | None = PlayerId.PLAYER1
    target: object | None = None


def _make_card(card_id: str, zone: CardPosition, index: int) -> FakeCard:
    return FakeCard(id=card_id, name=card_id, cardPosition=zone, index=index)


def _make_state() -> tuple[FakeState, FakePlayer, FakePlayer]:
    p1 = FakePlayer(id=PlayerId.PLAYER1)
    p2 = FakePlayer(id=PlayerId.PLAYER2)
    p1.hand = [_make_card("hand-1", CardPosition.HAND, 1), _make_card("hand-2", CardPosition.HAND, 2)]
    p1.left = [_make_card("left-1", CardPosition.LEFT, 1), _make_card("left-2", CardPosition.LEFT, 2)]
    p1.discard = [_make_card("discard-1", CardPosition.DISCARD, 1)]
    p1.prize = [_make_card("prize-1", CardPosition.PRIZE, 1)]
    p1.active = [
        FakePokemon(
            id="active-1",
            name="active-1",
            cardPosition=CardPosition.ACTIVE,
            index=1,
            position=PokemonPosition.ACTIVE,
        )
    ]
    state = FakeState(player1=p1, player2=p2, auto_events=["legacy-event"])
    return state, p1, p2


class _ReduceGuardMixin:
    def __init__(self) -> None:
        self.reduce_called = False

    def reduce_action(self, action, state):
        self.reduce_called = True
        raise AssertionError("SemanticReducerBridge 不应调用 legacy reduce_action")


class FakeSourceEmpty(_ReduceGuardMixin):
    def __init__(self) -> None:
        super().__init__()

    def resolve_ops(self, ctx: ResolverContext) -> list:
        return []


class FakeSourceMove(_ReduceGuardMixin):
    def __init__(self) -> None:
        super().__init__()

    def resolve_ops(self, ctx: ResolverContext):
        card = ctx.acting_player.left[0]
        from ptcg.core.ops import GameOp

        return [
            GameOp(
                type=OpType.MOVE_CARDS,
                category=OpCategory.STATE_OP,
                actor=PlayerSide.SELF,
                source=ZoneRef(PlayerSide.SELF, ZoneName.LEFT),
                target=ZoneRef(PlayerSide.SELF, ZoneName.HAND),
                params={"cards": card},
            )
        ]


class FakeSourceDraw(_ReduceGuardMixin):
    def __init__(self) -> None:
        super().__init__()

    def resolve_ops(self, ctx: ResolverContext):
        from ptcg.core.ops import GameOp

        return [GameOp(type=OpType.DRAW_CARDS, category=OpCategory.STATE_OP, actor=PlayerSide.SELF, params={"count": 1})]


class FakeSourceDiscard(_ReduceGuardMixin):
    def __init__(self) -> None:
        super().__init__()

    def resolve_ops(self, ctx: ResolverContext):
        from ptcg.core.ops import GameOp

        return [
            GameOp(
                type=OpType.DISCARD_CARDS,
                category=OpCategory.STATE_OP,
                actor=PlayerSide.SELF,
                params={"cards": [ctx.acting_player.hand[0]]},
            )
        ]


class FakeSourceInvalid(_ReduceGuardMixin):
    def __init__(self) -> None:
        super().__init__()

    def resolve_ops(self, ctx: ResolverContext):
        return {"invalid": True}


class FakeSourceUnsupported(_ReduceGuardMixin):
    def __init__(self) -> None:
        super().__init__()

    def resolve_ops(self, ctx: ResolverContext):
        from ptcg.core.ops import GameOp

        return [GameOp(type=OpType.DEAL_DAMAGE, category=OpCategory.STATE_OP, actor=PlayerSide.SELF)]


class FakeExecutorNoCall:
    def __init__(self) -> None:
        self.called = False

    def execute_ops(self, ctx, ops):
        self.called = True
        raise AssertionError("fallback 场景不应执行 executor")


class FakeExecutorRaises:
    def execute_ops(self, ctx, ops):
        raise InvalidOperationError("executor unsupported")


class FakeSourceWithoutResolve:
    pass


class TestSemanticReducerBridge:
    def test_source_without_resolve_ops_returns_fallback(self):
        state, _, _ = _make_state()
        executor = FakeExecutorNoCall()
        bridge = SemanticReducerBridge(executor=executor)

        result = bridge.reduce(FakeAction(source=FakeSourceWithoutResolve()), state)

        assert result.used_semantic is False
        assert result.fallback_required is True
        assert result.reason == "source_has_no_resolve_ops"
        assert executor.called is False

    def test_resolve_ops_returning_empty_returns_fallback(self):
        state, _, _ = _make_state()
        executor = FakeExecutorNoCall()
        bridge = SemanticReducerBridge(executor=executor)

        result = bridge.reduce(FakeAction(source=FakeSourceEmpty()), state)

        assert result.used_semantic is False
        assert result.fallback_required is True
        assert result.reason == "resolver_returned_empty"
        assert executor.called is False

    def test_resolve_ops_move_cards_uses_semantic_execution(self):
        state, player, _ = _make_state()
        source = FakeSourceMove()
        bridge = SemanticReducerBridge()

        result = bridge.reduce(FakeAction(source=source), state)

        assert result.used_semantic is True
        assert result.fallback_required is False
        assert [card.id for card in player.hand] == ["hand-1", "hand-2", "left-1"]
        assert [card.id for card in player.left] == ["left-2"]
        assert result.events[0].event_type == OperationEventType.CARDS_MOVED
        assert source.reduce_called is False

    def test_resolve_ops_draw_cards_uses_semantic_execution(self):
        state, player, _ = _make_state()
        bridge = SemanticReducerBridge()

        result = bridge.reduce(FakeAction(source=FakeSourceDraw()), state)

        assert result.used_semantic is True
        assert [card.id for card in player.hand] == ["hand-1", "hand-2", "left-1"]
        assert [card.id for card in player.left] == ["left-2"]

    def test_resolve_ops_discard_cards_uses_semantic_execution(self):
        state, player, _ = _make_state()
        bridge = SemanticReducerBridge()

        result = bridge.reduce(FakeAction(source=FakeSourceDiscard()), state)

        assert result.used_semantic is True
        assert [card.id for card in player.hand] == ["hand-2"]
        assert [card.id for card in player.discard] == ["discard-1", "hand-1"]

    def test_semantic_execution_does_not_call_reduce_action(self):
        state, _, _ = _make_state()
        source = FakeSourceMove()
        bridge = SemanticReducerBridge()

        bridge.reduce(FakeAction(source=source), state)

        assert source.reduce_called is False

    def test_resolve_ops_invalid_object_raises(self):
        state, _, _ = _make_state()
        bridge = SemanticReducerBridge()

        with pytest.raises(InvalidOperationError):
            bridge.reduce(FakeAction(source=FakeSourceInvalid()), state)

    def test_unsupported_op_raises_and_does_not_fallback(self):
        state, _, _ = _make_state()
        bridge = SemanticReducerBridge()

        with pytest.raises(InvalidOperationError):
            bridge.reduce(FakeAction(source=FakeSourceUnsupported()), state)

    def test_bridge_does_not_modify_auto_events(self):
        state, _, _ = _make_state()
        bridge = SemanticReducerBridge()

        bridge.reduce(FakeAction(source=FakeSourceMove()), state)

        assert state.auto_events == ["legacy-event"]

    def test_bridge_result_collects_events(self):
        state, _, _ = _make_state()
        bridge = SemanticReducerBridge()

        result = bridge.reduce(FakeAction(source=FakeSourceDraw()), state)

        assert len(result.events) == 1
        assert result.events[0].event_type == OperationEventType.CARDS_MOVED

    def test_should_fallback_to_legacy_returns_correct_bool(self):
        fallback_result = BridgeResult(used_semantic=False, fallback_required=True)
        semantic_result = BridgeResult(used_semantic=True, fallback_required=False)

        assert SemanticReducerBridge.should_fallback_to_legacy(fallback_result) is True
        assert SemanticReducerBridge.should_fallback_to_legacy(semantic_result) is False

    def test_executor_error_is_not_converted_to_fallback(self):
        state, _, _ = _make_state()
        bridge = SemanticReducerBridge(executor=FakeExecutorRaises())

        with pytest.raises(InvalidOperationError):
            bridge.reduce(FakeAction(source=FakeSourceDraw()), state)
