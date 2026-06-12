from dataclasses import dataclass, field

import pytest

from ptcg.core.enums import CardPosition, PlayerId, PokemonPosition
from ptcg.core.ops import (
    EventSink,
    ExecutionContext,
    GameOp,
    InvalidOperationError,
    OpCategory,
    OperationEventType,
    OperationExecutor,
    OpType,
    PlayerSide,
    ZoneName,
    ZoneRef,
)


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
    active: list[FakePokemon] = field(default_factory=list)
    bench: list[FakePokemon] = field(default_factory=list)
    lostZone: list[FakeCard] = field(default_factory=list)
    supporterPlayedTurn: bool = False


@dataclass
class FakeState:
    player1: FakePlayer
    player2: FakePlayer
    stadium: list[FakeCard] = field(default_factory=list)
    auto_events: list[str] = field(default_factory=list)


def _make_card(card_id: str, zone: CardPosition, index: int) -> FakeCard:
    return FakeCard(id=card_id, name=card_id, cardPosition=zone, index=index)


def _make_ctx() -> tuple[ExecutionContext, FakePlayer, FakePlayer, FakeState]:
    p1 = FakePlayer(id=PlayerId.PLAYER1)
    p2 = FakePlayer(id=PlayerId.PLAYER2)
    p1.hand = [_make_card("hand-1", CardPosition.HAND, 1), _make_card("hand-2", CardPosition.HAND, 2)]
    p1.left = [_make_card("left-1", CardPosition.LEFT, 1), _make_card("left-2", CardPosition.LEFT, 2)]
    p1.discard = [_make_card("discard-1", CardPosition.DISCARD, 1)]
    state = FakeState(player1=p1, player2=p2)
    ctx = ExecutionContext(state=state, acting_player=p1, opponent_player=p2)
    return ctx, p1, p2, state


def _make_executor() -> OperationExecutor:
    return OperationExecutor(event_sink=EventSink())


class TestOperationExecutor:
    def test_execute_op_mark_supporter_played_sets_flag_and_emits_event(self):
        ctx, player, _, _ = _make_ctx()
        executor = _make_executor()
        op = GameOp(
            type=OpType.MARK_SUPPORTER_PLAYED,
            category=OpCategory.STATE_OP,
            actor=PlayerSide.SELF,
        )

        result = executor.execute_op(ctx, op)

        assert result.success is True
        assert player.supporterPlayedTurn is True
        assert len(result.events) == 1
        assert result.events[0].event_type == OperationEventType.SUPPORTER_PLAYED_MARKED
        assert result.events[0].payload == {"field": "supporterPlayedTurn", "value": True}

    def test_execute_op_move_cards_moves_one_card_from_left_to_hand(self):
        ctx, player, _, _ = _make_ctx()
        executor = _make_executor()
        card = player.left[0]
        op = GameOp(
            type=OpType.MOVE_CARDS,
            category=OpCategory.STATE_OP,
            actor=PlayerSide.SELF,
            source=ZoneRef(PlayerSide.SELF, ZoneName.LEFT),
            target=ZoneRef(PlayerSide.SELF, ZoneName.HAND),
            params={"cards": card},
        )

        result = executor.execute_op(ctx, op)

        assert result.success is True
        assert card in player.hand
        assert card not in player.left

    def test_execute_op_draw_cards_draws_requested_count(self):
        ctx, player, _, _ = _make_ctx()
        executor = _make_executor()
        op = GameOp(
            type=OpType.DRAW_CARDS,
            category=OpCategory.STATE_OP,
            actor=PlayerSide.SELF,
            params={"count": 2},
        )

        result = executor.execute_op(ctx, op)

        assert result.payload == {"requested_count": 2, "actual_count": 2}
        assert [card.id for card in player.hand] == ["hand-1", "hand-2", "left-1", "left-2"]
        assert player.left == []

    def test_draw_cards_when_insufficient_deck_uses_actual_remaining(self):
        ctx, player, _, _ = _make_ctx()
        executor = _make_executor()
        op = GameOp(
            type=OpType.DRAW_CARDS,
            category=OpCategory.STATE_OP,
            actor=PlayerSide.SELF,
            params={"count": 3},
        )

        result = executor.execute_op(ctx, op)

        assert result.payload == {"requested_count": 3, "actual_count": 2}
        assert len(player.hand) == 4
        assert len(player.left) == 0

    def test_execute_op_discard_cards_count_all_discards_entire_hand(self):
        ctx, player, _, _ = _make_ctx()
        executor = _make_executor()
        op = GameOp(
            type=OpType.DISCARD_CARDS,
            category=OpCategory.STATE_OP,
            actor=PlayerSide.SELF,
            params={"count": "all"},
        )

        result = executor.execute_op(ctx, op)

        assert result.success is True
        assert player.hand == []
        assert [card.id for card in player.discard] == ["discard-1", "hand-1", "hand-2"]

    def test_execute_op_discard_cards_discards_specific_cards(self):
        ctx, player, _, _ = _make_ctx()
        executor = _make_executor()
        chosen = [player.hand[1]]
        op = GameOp(
            type=OpType.DISCARD_CARDS,
            category=OpCategory.STATE_OP,
            actor=PlayerSide.SELF,
            params={"cards": chosen},
        )

        result = executor.execute_op(ctx, op)

        assert result.success is True
        assert [card.id for card in player.hand] == ["hand-1"]
        assert [card.id for card in player.discard] == ["discard-1", "hand-2"]

    def test_discard_cards_numeric_count_without_cards_raises(self):
        ctx, _, _, _ = _make_ctx()
        executor = _make_executor()
        op = GameOp(
            type=OpType.DISCARD_CARDS,
            category=OpCategory.STATE_OP,
            actor=PlayerSide.SELF,
            params={"count": 2},
        )

        with pytest.raises(InvalidOperationError):
            executor.execute_op(ctx, op)

    def test_unsupported_op_raises_invalid_operation(self):
        ctx, _, _, _ = _make_ctx()
        executor = _make_executor()
        op = GameOp(
            type=OpType.DEAL_DAMAGE,
            category=OpCategory.STATE_OP,
            actor=PlayerSide.SELF,
        )

        with pytest.raises(InvalidOperationError):
            executor.execute_op(ctx, op)

    def test_execute_ops_runs_in_order(self):
        ctx, player, _, _ = _make_ctx()
        executor = _make_executor()
        first = GameOp(
            type=OpType.DRAW_CARDS,
            category=OpCategory.STATE_OP,
            actor=PlayerSide.SELF,
            order=2,
            params={"count": 1},
        )
        second = GameOp(
            type=OpType.DISCARD_CARDS,
            category=OpCategory.STATE_OP,
            actor=PlayerSide.SELF,
            order=1,
            params={"cards": [player.hand[0]]},
        )

        results = executor.execute_ops(ctx, [first, second])

        assert [result.op.order for result in results] == [1, 2]
        assert [card.id for card in player.discard] == ["discard-1", "hand-1"]
        assert [card.id for card in player.hand] == ["hand-2", "left-1"]

    def test_event_sink_receives_events(self):
        ctx, _, _, _ = _make_ctx()
        sink = EventSink()
        executor = OperationExecutor(event_sink=sink)
        op = GameOp(
            type=OpType.DRAW_CARDS,
            category=OpCategory.STATE_OP,
            actor=PlayerSide.SELF,
            params={"count": 1},
        )

        executor.execute_op(ctx, op)

        events = sink.list_events()
        assert len(events) == 1
        assert events[0].event_type == OperationEventType.CARDS_MOVED

    def test_executor_does_not_modify_auto_events(self):
        ctx, _, _, state = _make_ctx()
        executor = _make_executor()
        op = GameOp(
            type=OpType.DRAW_CARDS,
            category=OpCategory.STATE_OP,
            actor=PlayerSide.SELF,
            params={"count": 1},
        )

        executor.execute_op(ctx, op)

        assert state.auto_events == []
