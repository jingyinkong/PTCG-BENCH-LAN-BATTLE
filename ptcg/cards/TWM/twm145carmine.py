"""Carmine - TWM 145"""
from ptcg.core.action import UseSupporterAction
from ptcg.core.card import SupporterCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.core.ops import GameOp, OpCategory, OpType, PlayerSide, ZoneName, ZoneRef
from ptcg.utils.utils import current_player, move_cards


class TWM145Carmine(SupporterCard):
    """Carmine - Supporter. Discard hand, draw 5."""
    def __init__(self):
        super().__init__()
        self.set_name = "TWM"
        self.number = "145"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "丹瑜"
        self.cardType = CardType.NONE
        self.text = "将自己的所有手牌丢弃，然后从自己的牌库上方抽取5张。"

    def get_actions(self, state):
        actions = []
        player = current_player(state)
        if not player.supporterPlayedTurn:
            actions.append(UseSupporterAction(state.turn, self))
        return actions

    def resolve_ops(self, ctx):
        return [
            GameOp(
                type=OpType.MOVE_CARDS,
                category=OpCategory.STATE_OP,
                actor=PlayerSide.SELF,
                order=1,
                source=ZoneRef(PlayerSide.SELF, ZoneName.HAND),
                target=ZoneRef(PlayerSide.SELF, ZoneName.DISCARD),
                params={"cards": self},
            ),
            GameOp(
                type=OpType.DISCARD_CARDS,
                category=OpCategory.STATE_OP,
                actor=PlayerSide.SELF,
                order=2,
                source=ZoneRef(PlayerSide.SELF, ZoneName.HAND),
                target=ZoneRef(PlayerSide.SELF, ZoneName.DISCARD),
                params={"count": "all"},
            ),
            GameOp(
                type=OpType.DRAW_CARDS,
                category=OpCategory.STATE_OP,
                actor=PlayerSide.SELF,
                order=3,
                source=ZoneRef(PlayerSide.SELF, ZoneName.LEFT),
                target=ZoneRef(PlayerSide.SELF, ZoneName.HAND),
                params={"count": 5},
            ),
        ]

    def reduce_action(self, action, state):
        if isinstance(action, UseSupporterAction):
            player = current_player(state)
            move_cards(self, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state)
            for card in list(player.hand):
                move_cards(card, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state)
            for _ in range(min(5, len(player.left))):
                move_cards(player.left[0], (player.id, CardPosition.LEFT), (player.id, CardPosition.HAND), state)
            player.supporterPlayedTurn = True
