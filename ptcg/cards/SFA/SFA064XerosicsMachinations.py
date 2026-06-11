"""库瑟洛斯奇的企图 - SFA 064"""
from ptcg.core.action import UseSupporterAction
from ptcg.core.card import SupporterCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.utils.utils import current_player, move_cards


class SFA064XerosicsMachinations(SupporterCard):
    """库瑟洛斯奇的企图 - 支援者卡。"""
    def __init__(self):
        super().__init__()
        self.set_name = "SFA"
        self.number = "064"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "库瑟洛斯奇的企图"
        self.cardType = CardType.NONE
        self.text = "对手将对手自己的手牌放于弃牌区，直到手牌变为3张为止。"

    def get_actions(self, state):
        actions = []
        player = current_player(state)
        if not player.supporterPlayedTurn:
            actions.append(UseSupporterAction(state.turn, self))
        return actions

    def reduce_action(self, action, state):
        if isinstance(action, UseSupporterAction):
            player = current_player(state)
            move_cards(self, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state)
            player.supporterPlayedTurn = True
            yield None