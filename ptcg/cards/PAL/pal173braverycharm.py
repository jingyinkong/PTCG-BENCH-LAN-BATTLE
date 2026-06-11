"""勇气护符 - PAL 173"""
from ptcg.core.action import UseItemAction
from ptcg.core.card import ToolCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.utils.utils import current_player, move_cards


class PAL173BraveryCharm(ToolCard):
    """勇气护符 - 宝可梦道具卡。"""
    def __init__(self):
        super().__init__()
        self.set_name = "PAL"
        self.number = "173"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "勇气护符"
        self.cardType = CardType.NONE
        self.text = "身上放有这张卡牌的【基础】宝可梦的最大HP「+50」。"

    def get_actions(self, state):
        actions = []
        player = current_player(state)
        if self in player.hand:
            actions.append(UseItemAction(player.id, self))
        return actions

    def reduce_action(self, action, state):
        if isinstance(action, UseItemAction):
            player = current_player(state)
            move_cards(self, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state)
