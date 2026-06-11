from __future__ import annotations

from typing import Any, Iterable

from ptcg.core.card import PokemonCard
from ptcg.core.enums import CardPosition, PokemonPosition
from ptcg.core.ops.context import ExecutionContext
from ptcg.core.ops.errors import InvalidZoneError, OperationPreconditionError
from ptcg.core.ops.events import EventVisibility, OperationEvent, OperationEventType
from ptcg.core.ops.types import PlayerSide, ZoneName, ZoneRef


class ZoneService:
    """旁路区域服务，供后续 OperationExecutor 使用。"""

    _SAFE_LIST_ZONES = {
        ZoneName.HAND,
        ZoneName.LEFT,
        ZoneName.DISCARD,
        ZoneName.PRIZE,
        ZoneName.BENCH,
        ZoneName.LOST_ZONE,
    }

    _CARD_POSITION_MAP = {
        ZoneName.HAND: CardPosition.HAND,
        ZoneName.LEFT: CardPosition.LEFT,
        ZoneName.DISCARD: CardPosition.DISCARD,
        ZoneName.PRIZE: CardPosition.PRIZE,
        ZoneName.BENCH: CardPosition.BENCH,
        ZoneName.LOST_ZONE: CardPosition.LOSTZONE,
    }

    @classmethod
    def resolve_player(cls, ctx_or_state: Any, side: PlayerSide) -> Any:
        """根据 self/opponent 解析玩家对象。

        当前阶段不推断 current_player；如果没有显式上下文，则要求调用方自己提供。
        """

        if isinstance(ctx_or_state, ExecutionContext):
            if side == PlayerSide.SELF:
                if ctx_or_state.acting_player is None:
                    raise OperationPreconditionError("ExecutionContext 缺少 acting_player。")
                return ctx_or_state.acting_player
            if ctx_or_state.opponent_player is None:
                raise OperationPreconditionError("ExecutionContext 缺少 opponent_player。")
            return ctx_or_state.opponent_player

        raise NotImplementedError("ZoneService.resolve_player 目前需要显式传入 ExecutionContext。")

    @classmethod
    def resolve_zone(cls, ctx: ExecutionContext, zone_ref: ZoneRef) -> Any:
        """解析 ZoneRef 到当前工程中的真实区域对象。

        说明：
        - `deck` 对应初始牌组配置语义，运行时移动应优先使用 `left`。
        - `active` 在当前工程里是长度 0/1 的 list。
        - `attachment` 在当前阶段仅支持显式索引：0 表示 active，>=1 表示第 N 个 bench。
        """

        player = cls.resolve_player(ctx, zone_ref.side)

        if zone_ref.zone == ZoneName.HAND:
            return player.hand
        if zone_ref.zone == ZoneName.LEFT:
            return player.left
        if zone_ref.zone == ZoneName.DECK:
            if not hasattr(player, "deck"):
                raise InvalidZoneError("当前玩家没有 deck 字段。")
            return player.deck
        if zone_ref.zone == ZoneName.DISCARD:
            return player.discard
        if zone_ref.zone == ZoneName.PRIZE:
            return player.prize
        if zone_ref.zone == ZoneName.ACTIVE:
            return player.active
        if zone_ref.zone == ZoneName.BENCH:
            return player.bench
        if zone_ref.zone == ZoneName.STADIUM:
            return ctx.state.stadium
        if zone_ref.zone == ZoneName.LOST_ZONE:
            return cls._get_lost_zone(player)
        if zone_ref.zone == ZoneName.ATTACHMENT:
            return cls._resolve_attachment_zone(player, zone_ref)

        raise InvalidZoneError(f"不支持的区域类型: {zone_ref.zone}")

    @classmethod
    def count_cards(cls, ctx: ExecutionContext, zone_ref: ZoneRef) -> int:
        zone = cls.resolve_zone(ctx, zone_ref)
        if zone_ref.zone == ZoneName.ACTIVE:
            return 1 if len(zone) > 0 else 0
        return len(zone)

    @classmethod
    def contains_card(cls, ctx: ExecutionContext, zone_ref: ZoneRef, card: Any) -> bool:
        zone = cls.resolve_zone(ctx, zone_ref)
        return card in zone

    @classmethod
    def move_cards(
        cls,
        ctx: ExecutionContext,
        cards: Any,
        source: ZoneRef,
        target: ZoneRef,
        public: bool = False,
    ) -> OperationEvent:
        """在安全 list 区域间移动卡牌，不替换 legacy move_cards。"""

        cls._ensure_safe_move_zone(source)
        cls._ensure_safe_move_zone(target)

        source_zone = cls.resolve_zone(ctx, source)
        target_zone = cls.resolve_zone(ctx, target)

        if not isinstance(source_zone, list) or not isinstance(target_zone, list):
            raise OperationPreconditionError("ZoneService.move_cards 仅支持 list 型区域。")

        cards_to_move = cls._normalize_cards(cards)
        if len(cards_to_move) == 0:
            raise OperationPreconditionError("move_cards 需要至少一张卡。")

        for card in cards_to_move:
            if card not in source_zone:
                raise InvalidZoneError(f"卡牌不在源区域中: {cls.format_zone_ref(source)}")

        for card in cards_to_move:
            source_zone.remove(card)

        target_zone.extend(cards_to_move)

        cls._refresh_indices(source_zone)
        cls._refresh_indices(target_zone)
        cls._update_moved_cards(cards_to_move, target)

        visibility = EventVisibility.PUBLIC if public else EventVisibility.PRIVATE
        card_ids = [str(card_id) for card_id in cls._collect_card_ids(cards_to_move)]
        return OperationEvent(
            event_type=OperationEventType.CARDS_MOVED,
            source=cls.format_zone_ref(source),
            target=cls.format_zone_ref(target),
            count=len(cards_to_move),
            card_ids=card_ids,
            visibility=visibility,
        )

    @staticmethod
    def format_zone_ref(zone_ref: ZoneRef) -> str:
        return f"{zone_ref.side.value}.{zone_ref.zone.value}"

    @classmethod
    def _ensure_safe_move_zone(cls, zone_ref: ZoneRef) -> None:
        if zone_ref.zone not in cls._SAFE_LIST_ZONES:
            raise OperationPreconditionError(
                f"阶段2仅支持安全 list 区域移动，当前区域不支持: {cls.format_zone_ref(zone_ref)}"
            )

    @staticmethod
    def _normalize_cards(cards: Any) -> list[Any]:
        if isinstance(cards, list):
            return list(cards)
        if isinstance(cards, tuple):
            return list(cards)
        return [cards]

    @staticmethod
    def _refresh_indices(cards: Iterable[Any]) -> None:
        for idx, card in enumerate(cards, start=1):
            if hasattr(card, "index"):
                card.index = idx

    @classmethod
    def _update_moved_cards(cls, cards: list[Any], target: ZoneRef) -> None:
        target_position = cls._CARD_POSITION_MAP[target.zone]
        for card in cards:
            if hasattr(card, "cardPosition"):
                card.cardPosition = target_position
            if isinstance(card, PokemonCard) and target.zone == ZoneName.BENCH:
                card.position = PokemonPosition.BENCH

    @staticmethod
    def _collect_card_ids(cards: list[Any]) -> list[str]:
        card_ids: list[str] = []
        for card in cards:
            if hasattr(card, "id") and getattr(card, "id") is not None:
                card_ids.append(str(card.id))
        return card_ids

    @staticmethod
    def _get_lost_zone(player: Any) -> Any:
        if hasattr(player, "lostZone"):
            return player.lostZone
        if hasattr(player, "lost_zone"):
            return player.lost_zone
        raise InvalidZoneError("当前玩家没有 lostZone/lost_zone 字段。")

    @staticmethod
    def _resolve_attachment_zone(player: Any, zone_ref: ZoneRef) -> Any:
        if zone_ref.index is None:
            raise OperationPreconditionError("attachment 区域需要显式 index；0 表示 active，>=1 表示 bench。")

        if zone_ref.index == 0:
            if len(player.active) == 0:
                raise OperationPreconditionError("active 为空，无法解析 attachment。")
            return player.active[0].attachment

        bench_idx = zone_ref.index - 1
        if bench_idx < 0 or bench_idx >= len(player.bench):
            raise InvalidZoneError("attachment 对应的 bench index 超出范围。")
        return player.bench[bench_idx].attachment
