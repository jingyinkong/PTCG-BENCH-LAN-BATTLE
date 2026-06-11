"""重力山 - SSP 177"""
from ptcg.core.action import PutStadiumAction, DiscardStadiumAction
from ptcg.core.card import StadiumCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.utils.utils import current_player, move_cards


class SSP177GravityMountain(StadiumCard):
    """重力山 - 场地卡。"""
    def __init__(self):
        super().__init__()
        self.set_name = "SSP"
        self.number = "177"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "重力山"
        self.cardType = CardType.NONE
        self.text = "双方场上的所有【2阶进化】宝可梦的最大HP，各「-30」。"

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
