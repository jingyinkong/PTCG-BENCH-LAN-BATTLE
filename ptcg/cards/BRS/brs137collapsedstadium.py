"""崩塌的竞技场 - BRS 137"""
from ptcg.core.action import PutStadiumAction, DiscardStadiumAction
from ptcg.core.card import StadiumCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.utils.utils import current_player, move_cards


class BRS137CollapsedStadium(StadiumCard):
    """崩塌的竞技场 - 场地卡。"""
    def __init__(self):
        super().__init__()
        self.set_name = "BRS"
        self.number = "137"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "崩塌的竞技场"
        self.cardType = CardType.NONE
        self.text = "双方玩家可以放于备战区的宝可梦数量，变为4只。［关于变更备战宝可梦的数量的效果，优先执行数量更少的效果。］  （当这张卡牌被放于场上时，备战区有5只以上宝可梦（包含5只）的玩家，将宝可梦放于弃牌区直到备战区宝可梦变为4只为止。放于弃牌区的动作由这张卡牌的持有者开始执行。）"

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
