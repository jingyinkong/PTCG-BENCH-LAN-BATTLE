from dataclasses import dataclass, field

from ptcg.cards.TWM.twm145carmine import TWM145Carmine
from ptcg.core.action import UseSupporterAction
from ptcg.core.enums import CardPosition, PlayerId
from ptcg.core.ops import (
    OpType,
    OperationEventType,
    OperationResolver,
    ResolverContext,
    SemanticReducerBridge,
)


@dataclass
class FakeCard:
    id: str
    name: str
    cardPosition: CardPosition
    index: int = 0


@dataclass
class FakePlayer:
    id: PlayerId
    hand: list[object] = field(default_factory=list)
    left: list[object] = field(default_factory=list)
    discard: list[object] = field(default_factory=list)
    supporterPlayedTurn: bool = False


@dataclass
class FakeState:
    turn: PlayerId
    player1: FakePlayer
    player2: FakePlayer
    auto_events: list[str] = field(default_factory=list)
    stadium: list[object] = field(default_factory=list)


def _make_cards(prefix: str, zone: CardPosition, count: int) -> list[FakeCard]:
    return [
        FakeCard(
            id=f"{prefix}-{idx}",
            name=f"{prefix}-{idx}",
            cardPosition=zone,
            index=idx,
        )
        for idx in range(1, count + 1)
    ]


def _zone_ids(cards: list[object]) -> list[str]:
    return [card.id for card in cards]


def _make_carmine_fixture():
    player = FakePlayer(id=PlayerId.PLAYER1)
    opponent = FakePlayer(id=PlayerId.PLAYER2)
    state = FakeState(turn=PlayerId.PLAYER1, player1=player, player2=opponent)

    carmine = TWM145Carmine()
    carmine.cardPosition = CardPosition.HAND
    carmine.index = 1

    other_hand = _make_cards("hand", CardPosition.HAND, 2)
    deck_cards = _make_cards("left", CardPosition.LEFT, 6)

    player.hand = [carmine, *other_hand]
    player.left = deck_cards

    for idx, card in enumerate(player.hand, start=1):
        card.index = idx

    action = UseSupporterAction(player.id, carmine)
    return state, player, opponent, carmine, action, other_hand, deck_cards


def test_carmine_resolver_returns_expected_sidechannel_ops():
    state, player, opponent, carmine, action, _, _ = _make_carmine_fixture()
    resolver = OperationResolver()

    ops = resolver.resolve_action(
        ResolverContext(
            state=state,
            action=action,
            acting_player=player,
            opponent_player=opponent,
            source_card=carmine,
        )
    )

    assert callable(getattr(carmine, "reduce_action", None))
    assert [op.type for op in ops] == [
        OpType.MOVE_CARDS,
        OpType.DISCARD_CARDS,
        OpType.DRAW_CARDS,
        OpType.MARK_SUPPORTER_PLAYED,
    ]
    assert ops[0].params["cards"] is carmine
    assert ops[1].params == {"count": "all"}
    assert ops[2].params == {"count": 5}
    assert ops[3].params == {}


def test_carmine_semantic_bridge_executes_sidechannel_zone_changes():
    state, player, _, carmine, action, other_hand, deck_cards = _make_carmine_fixture()
    bridge = SemanticReducerBridge()
    original_hand_ids = [carmine.id, *_zone_ids(other_hand)]
    drawn_ids = _zone_ids(deck_cards[:5])
    remaining_left_ids = _zone_ids(deck_cards[5:])

    result = bridge.reduce(action, state)

    assert result.used_semantic is True
    assert result.fallback_required is False
    assert [op_result.op.type for op_result in result.op_results] == [
        OpType.MOVE_CARDS,
        OpType.DISCARD_CARDS,
        OpType.DRAW_CARDS,
        OpType.MARK_SUPPORTER_PLAYED,
    ]

    assert player.supporterPlayedTurn is True
    assert _zone_ids(player.discard) == original_hand_ids
    assert _zone_ids(player.hand) == drawn_ids
    assert _zone_ids(player.left) == remaining_left_ids
    assert len(player.left) == 1

    assert carmine in player.discard
    assert all(card in player.discard for card in other_hand)
    assert len(result.events) == 4
    assert [event.op_type for event in result.events] == [
        "move_cards",
        "discard_cards",
        "draw_cards",
        "mark_supporter_played",
    ]
    assert [event.event_type for event in result.events] == [
        OperationEventType.CARDS_MOVED,
        OperationEventType.CARDS_MOVED,
        OperationEventType.CARDS_MOVED,
        OperationEventType.SUPPORTER_PLAYED_MARKED,
    ]
    assert [event.count for event in result.events] == [1, 2, 5, None]
    assert state.auto_events == []
