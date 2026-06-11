"""丽姿 - BUS 119"""
from ptcg.core.action import UseSupporterAction
from ptcg.core.card import SupporterCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.utils.utils import current_player, move_cards


class BUS119Olivia(SupporterCard):
    """丽姿 - 支援者卡。"""
    def __init__(self):
        super().__init__()
        self.set_name = "BUS"
        self.number = "119"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "丽姿"
        self.cardType = CardType.NONE
        self.text = "将自己牌库中最多2张「宝可梦GX」，在给对手看过之后，加入手牌。并重洗牌库。"

    def get_actions(self, state):
        actions = []
        player = current_player(state)
        if self in player.hand and not player.supporterPlayedTurn:
            actions.append(UseSupporterAction(state.turn, self))
        return actions

    def reduce_action(self, action, state):
        if isinstance(action, UseSupporterAction):
            player = current_player(state)
            move_cards(self, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state)
            player.supporterPlayedTurn = True
            yield None