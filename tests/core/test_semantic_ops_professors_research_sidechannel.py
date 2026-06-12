from dataclasses import dataclass, field

from ptcg.cards.SSH.ssh178professorsresearch import SSH178ProfessorsResearch
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


def _make_professors_research_fixture():
    player = FakePlayer(id=PlayerId.PLAYER1)
    opponent = FakePlayer(id=PlayerId.PLAYER2)
    state = FakeState(turn=PlayerId.PLAYER1, player1=player, player2=opponent)

    professors_research = SSH178ProfessorsResearch()
    professors_research.cardPosition = CardPosition.HAND
    professors_research.index = 1

    other_hand = _make_cards("hand", CardPosition.HAND, 2)
    deck_cards = _make_cards("left", CardPosition.LEFT, 8)

    player.hand = [professors_research, *other_hand]
    player.left = deck_cards

    for idx, card in enumerate(player.hand, start=1):
        card.index = idx

    action = UseSupporterAction(player.id, professors_research)
    return state, player, opponent, professors_research, action, other_hand, deck_cards


def test_professors_research_resolver_returns_expected_sidechannel_ops():
    state, player, opponent, professors_research, action, _, _ = _make_professors_research_fixture()
    resolver = OperationResolver()

    ops = resolver.resolve_action(
        ResolverContext(
            state=state,
            action=action,
            acting_player=player,
            opponent_player=opponent,
            source_card=professors_research,
        )
    )

    assert callable(getattr(professors_research, "reduce_action", None))
    assert [op.type for op in ops] == [
        OpType.MOVE_CARDS,
        OpType.DISCARD_CARDS,
        OpType.DRAW_CARDS,
        OpType.MARK_SUPPORTER_PLAYED,
    ]
    assert ops[0].params["cards"] is professors_research
    assert ops[1].params == {"count": "all"}
    assert ops[2].params == {"count": 7}
    assert ops[3].params == {}


def test_professors_research_semantic_bridge_executes_sidechannel_zone_changes():
    state, player, _, professors_research, action, other_hand, deck_cards = _make_professors_research_fixture()
    bridge = SemanticReducerBridge()
    original_hand_ids = [professors_research.id, *_zone_ids(other_hand)]
    drawn_ids = _zone_ids(deck_cards[:7])
    remaining_left_ids = _zone_ids(deck_cards[7:])

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

    assert professors_research in player.discard
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
    assert [event.count for event in result.events] == [1, 2, 7, None]
    assert state.auto_events == []
