"""Area Zero Underdepths - SCR 131"""
from ptcg.core.action import PutStadiumAction, DiscardStadiumAction
from ptcg.core.card import StadiumCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.utils.utils import current_player, move_cards


class SCR131AreaZeroUnderdepths(StadiumCard):
    """Area Zero Underdepths - Stadium."""
    def __init__(self):
        super().__init__()
        self.set_name = "SCR"
        self.number = "131"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "零之大空洞"
        self.cardType = CardType.NONE
        self.text = "自己场上有「太晶」宝可梦的玩家，可以放于备战区的宝可梦数量变为8只。  （当这张卡牌被放于弃牌区，或者自己场上没有「太晶」宝可梦时，将备战宝可梦放于弃牌区，直到备战宝可梦的数量变为5只为止。双方都要将备战宝可梦放于弃牌区的话，则由这张卡牌的持有者开始执行。）"

    def get_actions(self, state):
        actions = []
        player = current_player(state)
        if not player.stadiumPlayedTurn and self in player.hand:
            actions.append(PutStadiumAction(player.id, self))
        return actions

    def reduce_action(self, action, state):
        player = current_player(state)
        if isinstance(action, PutStadiumAction):
            if state.stadium:
                old = state.stadium[0]
                try:
                    r = old.reduce_action(DiscardStadiumAction(old.playedFrom, old), state)
                    if r is not None:
                        yield from r
                except StopIteration:
                    pass
            self.playedFrom = player.id
            player.stadiumPlayedTurn = True
            move_cards(action.source, (player.id, CardPosition.HAND), (None, CardPosition.STADIUM), state)
