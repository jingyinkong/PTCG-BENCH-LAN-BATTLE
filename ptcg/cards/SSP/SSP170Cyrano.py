"""席蓝 - SSP 170"""
from ptcg.core.action import UseSupporterAction
from ptcg.core.card import SupporterCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.utils.utils import current_player, move_cards


class SSP170Cyrano(SupporterCard):
    """席蓝 - 支援者卡。"""
    def __init__(self):
        super().__init__()
        self.set_name = "SSP"
        self.number = "170"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "席蓝"
        self.cardType = CardType.NONE
        self.text = "选择自己牌库中最多3张「宝可梦【ex】」，在给对手看过之后，加入手牌。并重洗牌库。"

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