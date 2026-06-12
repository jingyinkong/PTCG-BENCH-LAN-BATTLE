from dataclasses import dataclass, field

import pytest

from ptcg.core.enums import CardPosition, PlayerId, PokemonPosition
from ptcg.core.ops import (
    GameOp,
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
    discard: list[FakeCard] = field(default_factory=list)
    prize: list[FakeCard] = field(default_factory=list)
    bench: list[FakePokemon] = field(default_factory=list)
    active: list[FakePokemon] = field(default_factory=list)
    lostZone: list[FakeCard] = field(default_factory=list)

    @property
    def lost_zone(self) -> list[FakeCard]:
        return self.lostZone


@dataclass
class FakeState:
    player: FakePlayer
    opponent: FakePlayer
    auto_events: list[str] = field(default_factory=list)
    stadium: list[FakeCard] = field(default_factory=list)

    @property
    def player1(self) -> FakePlayer:
        return self.player

    @property
    def player2(self) -> FakePlayer:
        return self.opponent


@dataclass
class FakeAction:
    source: object | None
    playerId: PlayerId | None = PlayerId.PLAYER1
    target: object | None = None


def _make_cards(prefix: str, zone: CardPosition, count: int) -> list[FakeCard]:
    return [FakeCard(id=f"{prefix}-{idx}", name=f"{prefix}-{idx}", cardPosition=zone, index=idx) for idx in range(1, count + 1)]


def _make_state(hand_count: int = 0, left_count: int = 0, discard_count: int = 0) -> tuple[FakeState, FakePlayer, FakePlayer]:
    player = FakePlayer(id=PlayerId.PLAYER1)
    opponent = FakePlayer(id=PlayerId.PLAYER2)
    player.hand = _make_cards("hand", CardPosition.HAND, hand_count)
    player.left = _make_cards("left", CardPosition.LEFT, left_count)
    player.discard = _make_cards("discard", CardPosition.DISCARD, discard_count)
    player.prize = _make_cards("prize", CardPosition.PRIZE, 1)
    player.lostZone = _make_cards("lost", CardPosition.LOSTZONE, 1)
    player.active = [
        FakePokemon(
            id="active-1",
            name="active-1",
            cardPosition=CardPosition.ACTIVE,
            index=1,
            position=PokemonPosition.ACTIVE,
        )
    ]
    player.bench = [
        FakePokemon(
            id="bench-1",
            name="bench-1",
            cardPosition=CardPosition.BENCH,
            index=1,
            position=PokemonPosition.BENCH,
        )
    ]
    state = FakeState(player=player, opponent=opponent, auto_events=["legacy-event"])
    return state, player, opponent


def _snapshot_state(state: FakeState) -> dict[str, list[str]]:
    return {
        "hand": [card.id for card in state.player.hand],
        "left": [card.id for card in state.player.left],
        "discard": [card.id for card in state.player.discard],
        "prize": [card.id for card in state.player.prize],
        "bench": [card.id for card in state.player.bench],
        "active": [card.id for card in state.player.active],
        "lost_zone": [card.id for card in state.player.lostZone],
        "auto_events": list(state.auto_events),
    }


class _ReduceGuardMixin:
    def __init__(self) -> None:
        self.reduce_called = False

    def reduce_action(self, action, state):
        self.reduce_called = True
        raise AssertionError("fake integration 测试不应调用 legacy reduce_action")


class FakeSourceWithoutResolve(_ReduceGuardMixin):
    def __init__(self) -> None:
        super().__init__()


class FakeSourceEmpty(_ReduceGuardMixin):
    def __init__(self) -> None:
        super().__init__()

    def resolve_ops(self, ctx: ResolverContext) -> list[GameOp]:
        return []


class FakeSourceFactory(_ReduceGuardMixin):
    def __init__(self, op_factory):
        super().__init__()
        self.op_factory = op_factory
        self.seen_ctx: ResolverContext | None = None

    def resolve_ops(self, ctx: ResolverContext) -> list[GameOp]:
        self.seen_ctx = ctx
        return self.op_factory(ctx)


class TestSemanticOpsFakeIntegration:
    def test_move_cards_fake_integration_moves_card_from_left_to_hand(self):
        state, player, _ = _make_state(left_count=1)
        source = FakeSourceFactory(
            lambda ctx: [
                GameOp(
                    type=OpType.MOVE_CARDS,
                    category=OpCategory.STATE_OP,
                    actor=PlayerSide.SELF,
                    source=ZoneRef(PlayerSide.SELF, ZoneName.LEFT),
                    target=ZoneRef(PlayerSide.SELF, ZoneName.HAND),
                    params={"cards": ctx.acting_player.left[0]},
                )
            ]
        )
        bridge = SemanticReducerBridge()

        result = bridge.reduce(FakeAction(source=source), state)

        assert result.used_semantic is True
        assert result.fallback_required is False
        assert [card.id for card in player.left] == []
        assert [card.id for card in player.hand] == ["left-1"]
        assert len(result.events) == 1
        assert result.events[0].event_type == OperationEventType.CARDS_MOVED
        assert source.reduce_called is False
        assert state.auto_events == ["legacy-event"]

    def test_draw_cards_fake_integration_draws_requested_count(self):
        state, player, _ = _make_state(hand_count=1, left_count=3)
        source = FakeSourceFactory(
            lambda ctx: [
                GameOp(
                    type=OpType.DRAW_CARDS,
                    category=OpCategory.STATE_OP,
                    actor=PlayerSide.SELF,
                    params={"count": 2},
                )
            ]
        )
        bridge = SemanticReducerBridge()

        result = bridge.reduce(FakeAction(source=source), state)

        assert result.used_semantic is True
        assert len(player.hand) == 3
        assert len(player.left) == 1
        assert result.payload["op_types"] == ["draw_cards"]
        assert len(result.events) == 1
        assert result.events[0].count == 2
        assert source.reduce_called is False

    def test_discard_cards_fake_integration_discards_entire_hand(self):
        state, player, _ = _make_state(hand_count=2)
        source = FakeSourceFactory(
            lambda ctx: [
                GameOp(
                    type=OpType.DISCARD_CARDS,
                    category=OpCategory.STATE_OP,
                    actor=PlayerSide.SELF,
                    params={"count": "all"},
                )
            ]
        )
        bridge = SemanticReducerBridge()

        result = bridge.reduce(FakeAction(source=source), state)

        assert result.used_semantic is True
        assert result.fallback_required is False
        assert player.hand == []
        assert [card.id for card in player.discard] == ["hand-1", "hand-2"]
        assert source.reduce_called is False

    def test_multiple_ops_fake_integration_execute_in_order(self):
        state, player, _ = _make_state(left_count=3)
        source = FakeSourceFactory(
            lambda ctx: [
                GameOp(
                    type=OpType.DISCARD_CARDS,
                    category=OpCategory.STATE_OP,
                    actor=PlayerSide.SELF,
                    order=2,
                    params={"count": "all"},
                ),
                GameOp(
                    type=OpType.DRAW_CARDS,
                    category=OpCategory.STATE_OP,
                    actor=PlayerSide.SELF,
                    order=1,
                    params={"count": 2},
                ),
            ]
        )
        bridge = SemanticReducerBridge()

        result = bridge.reduce(FakeAction(source=source), state)

        assert [op_result.op.order for op_result in result.op_results] == [1, 2]
        assert player.hand == []
        assert [card.id for card in player.discard] == ["left-1", "left-2"]
        assert [card.id for card in player.left] == ["left-3"]
        assert source.reduce_called is False

    def test_fallback_without_resolve_ops_does_not_mutate_state(self):
        state, _, _ = _make_state(hand_count=1, left_count=1, discard_count=1)
        source = FakeSourceWithoutResolve()
        before = _snapshot_state(state)
        bridge = SemanticReducerBridge()

        result = bridge.reduce(FakeAction(source=source), state)

        assert result.fallback_required is True
        assert result.used_semantic is False
        assert _snapshot_state(state) == before
        assert source.reduce_called is False
        assert state.auto_events == ["legacy-event"]

    def test_empty_resolve_ops_returns_fallback_without_mutating_state(self):
        state, _, _ = _make_state(hand_count=1, left_count=2, discard_count=1)
        source = FakeSourceEmpty()
        before = _snapshot_state(state)
        bridge = SemanticReducerBridge()

        result = bridge.reduce(FakeAction(source=source), state)

        assert result.fallback_required is True
        assert result.used_semantic is False
        assert result.reason == "resolver_returned_empty"
        assert _snapshot_state(state) == before
        assert source.reduce_called is False

    @pytest.mark.parametrize("op_type", [OpType.DEAL_DAMAGE, OpType.CHOOSE_CARDS])
    def test_unsupported_ops_raise_without_mutating_state(self, op_type: OpType):
        state, _, _ = _make_state(hand_count=1, left_count=2, discard_count=1)
        source = FakeSourceFactory(
            lambda ctx: [GameOp(type=op_type, category=OpCategory.STATE_OP, actor=PlayerSide.SELF)]
        )
        before = _snapshot_state(state)
        bridge = SemanticReducerBridge()

        with pytest.raises(InvalidOperationError):
            bridge.reduce(FakeAction(source=source), state)

        assert _snapshot_state(state) == before
        assert source.reduce_called is False
        assert state.auto_events == ["legacy-event"]

    def test_requires_choice_op_raises_without_mutating_state(self):
        state, _, _ = _make_state(left_count=1)
        source = FakeSourceFactory(
            lambda ctx: [
                GameOp(
                    type=OpType.MOVE_CARDS,
                    category=OpCategory.STATE_OP,
                    actor=PlayerSide.SELF,
                    source=ZoneRef(PlayerSide.SELF, ZoneName.LEFT),
                    target=ZoneRef(PlayerSide.SELF, ZoneName.HAND),
                    params={"cards": ctx.acting_player.left[0]},
                    requires_choice=True,
                )
            ]
        )
        before = _snapshot_state(state)
        bridge = SemanticReducerBridge()

        with pytest.raises(InvalidOperationError, match="requires_choice=True"):
            bridge.reduce(FakeAction(source=source), state)

        assert _snapshot_state(state) == before
        assert source.reduce_called is False

    def test_conditioned_op_raises_without_mutating_state(self):
        state, _, _ = _make_state(left_count=1)
        source = FakeSourceFactory(
            lambda ctx: [
                GameOp(
                    type=OpType.MOVE_CARDS,
                    category=OpCategory.STATE_OP,
                    actor=PlayerSide.SELF,
                    source=ZoneRef(PlayerSide.SELF, ZoneName.LEFT),
                    target=ZoneRef(PlayerSide.SELF, ZoneName.HAND),
                    params={"cards": ctx.acting_player.left[0]},
                    condition={"if": "something"},
                )
            ]
        )
        before = _snapshot_state(state)
        bridge = SemanticReducerBridge()

        with pytest.raises(InvalidOperationError, match="condition"):
            bridge.reduce(FakeAction(source=source), state)

        assert _snapshot_state(state) == before
        assert source.reduce_called is False

    def test_draw_cards_fake_integration_emits_auditable_payload_and_events(self):
        state, _, _ = _make_state(left_count=2)
        source = FakeSourceFactory(
            lambda ctx: [
                GameOp(
                    type=OpType.DRAW_CARDS,
                    category=OpCategory.STATE_OP,
                    actor=PlayerSide.SELF,
                    params={"count": 2},
                )
            ]
        )
        bridge = SemanticReducerBridge()

        result = bridge.reduce(FakeAction(source=source), state)

        assert result.payload["action_type"] == "FakeAction"
        assert result.payload["source_type"] == "FakeSourceFactory"
        assert result.payload["used_semantic"] is True
        assert result.payload["fallback_required"] is False
        assert result.payload["op_count"] == 1
        assert result.payload["op_types"] == ["draw_cards"]
        assert result.payload["supported_ops_only"] is True
        assert result.payload["allow_generator"] is False
        assert result.payload["allow_choice"] is False
        assert len(result.events) == 1
        for event in result.events:
            assert event.event_type == OperationEventType.CARDS_MOVED
            assert event.source == "self.left"
            assert event.target == "self.hand"
            assert event.count == 2
        assert source.reduce_called is False
