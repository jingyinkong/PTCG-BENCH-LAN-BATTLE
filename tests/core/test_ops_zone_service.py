from dataclasses import dataclass, field

import pytest

from ptcg.core.enums import CardPosition, PlayerId, PokemonPosition
from ptcg.core.ops import (
    ExecutionContext,
    InvalidZoneError,
    OperationEventType,
    OperationPreconditionError,
    PlayerSide,
    ZoneName,
    ZoneRef,
    ZoneService,
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


@dataclass
class FakeState:
    player1: FakePlayer
    player2: FakePlayer
    stadium: list[FakeCard] = field(default_factory=list)


def _make_card(card_id: str, zone: CardPosition, index: int) -> FakeCard:
    return FakeCard(id=card_id, name=card_id, cardPosition=zone, index=index)


def _make_ctx() -> tuple[ExecutionContext, FakePlayer, FakePlayer]:
    p1 = FakePlayer(id=PlayerId.PLAYER1)
    p2 = FakePlayer(id=PlayerId.PLAYER2)

    p1.hand = [_make_card("hand-1", CardPosition.HAND, 1), _make_card("hand-2", CardPosition.HAND, 2)]
    p1.left = [_make_card("left-1", CardPosition.LEFT, 1), _make_card("left-2", CardPosition.LEFT, 2)]
    p1.discard = [_make_card("discard-1", CardPosition.DISCARD, 1)]
    p1.prize = [_make_card("prize-1", CardPosition.PRIZE, 1)]
    p1.lostZone = [_make_card("lost-1", CardPosition.LOSTZONE, 1)]
    p1.active = [
        FakePokemon(
            id="active-1",
            name="active-1",
            cardPosition=CardPosition.ACTIVE,
            index=1,
            position=PokemonPosition.ACTIVE,
            attachment=[_make_card("energy-a", CardPosition.ACTIVE_ATTACHMENT, 1)],
        )
    ]
    p1.bench = [
        FakePokemon(
            id="bench-1",
            name="bench-1",
            cardPosition=CardPosition.BENCH,
            index=1,
            position=PokemonPosition.BENCH,
            attachment=[_make_card("energy-b", CardPosition.BENCH_ATTACHMENT, 1)],
        )
    ]

    state = FakeState(player1=p1, player2=p2, stadium=[_make_card("stadium-1", CardPosition.STADIUM, 1)])
    ctx = ExecutionContext(state=state, acting_player=p1, opponent_player=p2)
    return ctx, p1, p2


class TestZoneService:
    def test_count_cards_counts_hand_left_discard(self):
        ctx, _, _ = _make_ctx()

        assert ZoneService.count_cards(ctx, ZoneRef(PlayerSide.SELF, ZoneName.HAND)) == 2
        assert ZoneService.count_cards(ctx, ZoneRef(PlayerSide.SELF, ZoneName.LEFT)) == 2
        assert ZoneService.count_cards(ctx, ZoneRef(PlayerSide.SELF, ZoneName.DISCARD)) == 1

    def test_contains_card_detects_membership(self):
        ctx, player, _ = _make_ctx()
        card = player.hand[0]

        assert ZoneService.contains_card(ctx, ZoneRef(PlayerSide.SELF, ZoneName.HAND), card) is True
        assert ZoneService.contains_card(ctx, ZoneRef(PlayerSide.SELF, ZoneName.DISCARD), card) is False

    def test_move_cards_moves_one_card_from_left_to_hand(self):
        ctx, player, _ = _make_ctx()
        card = player.left[0]

        event = ZoneService.move_cards(
            ctx,
            card,
            ZoneRef(PlayerSide.SELF, ZoneName.LEFT),
            ZoneRef(PlayerSide.SELF, ZoneName.HAND),
        )

        assert card in player.hand
        assert card not in player.left
        assert card.cardPosition == CardPosition.HAND
        assert [c.index for c in player.left] == [1]
        assert [c.index for c in player.hand] == [1, 2, 3]
        assert event.event_type == OperationEventType.CARDS_MOVED

    def test_move_cards_moves_multiple_cards_from_hand_to_discard(self):
        ctx, player, _ = _make_ctx()
        cards = list(player.hand)

        event = ZoneService.move_cards(
            ctx,
            cards,
            ZoneRef(PlayerSide.SELF, ZoneName.HAND),
            ZoneRef(PlayerSide.SELF, ZoneName.DISCARD),
        )

        assert player.hand == []
        assert [card.id for card in player.discard] == ["discard-1", "hand-1", "hand-2"]
        assert [card.index for card in player.discard] == [1, 2, 3]
        assert all(card.cardPosition == CardPosition.DISCARD for card in cards)
        assert event.count == 2

    def test_move_missing_card_raises(self):
        ctx, _, _ = _make_ctx()
        ghost = _make_card("ghost", CardPosition.HAND, 1)

        with pytest.raises(InvalidZoneError):
            ZoneService.move_cards(
                ctx,
                ghost,
                ZoneRef(PlayerSide.SELF, ZoneName.HAND),
                ZoneRef(PlayerSide.SELF, ZoneName.DISCARD),
            )

    def test_move_cards_returns_cards_moved_event(self):
        ctx, player, _ = _make_ctx()
        card = player.left[0]

        event = ZoneService.move_cards(
            ctx,
            card,
            ZoneRef(PlayerSide.SELF, ZoneName.LEFT),
            ZoneRef(PlayerSide.SELF, ZoneName.HAND),
        )

        assert event.event_type == OperationEventType.CARDS_MOVED
        assert event.count == 1
        assert event.source == "self.left"
        assert event.target == "self.hand"
        assert event.card_ids == ["left-1"]

    @pytest.mark.parametrize("zone_name", [ZoneName.ACTIVE, ZoneName.ATTACHMENT, ZoneName.STADIUM])
    def test_unsupported_move_zone_raises_precondition_error(self, zone_name: ZoneName):
        ctx, player, _ = _make_ctx()
        card = player.hand[0]

        with pytest.raises(OperationPreconditionError):
            ZoneService.move_cards(
                ctx,
                card,
                ZoneRef(PlayerSide.SELF, ZoneName.HAND),
                ZoneRef(PlayerSide.SELF, zone_name),
            )

    def test_resolve_zone_supports_active_attachment_and_stadium_reads(self):
        ctx, player, _ = _make_ctx()

        assert ZoneService.count_cards(ctx, ZoneRef(PlayerSide.SELF, ZoneName.ACTIVE)) == 1
        assert ZoneService.resolve_zone(ctx, ZoneRef(PlayerSide.SELF, ZoneName.ATTACHMENT, index=0)) == (
            player.active[0].attachment
        )
        assert ZoneService.count_cards(ctx, ZoneRef(PlayerSide.SELF, ZoneName.STADIUM)) == 1
