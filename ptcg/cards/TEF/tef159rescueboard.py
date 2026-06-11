"""紧急滑板 - TEF 159"""
from ptcg.core.action import UseItemAction
from ptcg.core.card import ToolCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.utils.utils import current_player, move_cards


class TEF159RescueBoard(ToolCard):
    """紧急滑板 - 宝可梦道具卡。"""
    def __init__(self):
        super().__init__()
        self.set_name = "TEF"
        self.number = "159"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "紧急滑板"
        self.cardType = CardType.NONE
        self.text = "身上放有这张卡牌的宝可梦，【撤退】所需能量减少1个。如果那只宝可梦的剩余HP在「30」及以下的话，则【撤退】所需能量，全部消除。"

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
