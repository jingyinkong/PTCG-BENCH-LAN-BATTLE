"""赤松 - SCR 133"""
from ptcg.core.action import UseSupporterAction
from ptcg.core.card import SupporterCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.utils.utils import current_player, move_cards


class SCR133Crispin(SupporterCard):
    """赤松 - 支援者卡。"""
    def __init__(self):
        super().__init__()
        self.set_name = "SCR"
        self.number = "133"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "赤松"
        self.cardType = CardType.NONE
        self.text = "选择自己牌库中，属性各不相同的基本能量最多2张，在给对手看过之后，将其中1张加入手牌，将剩余的能量附着于自己的宝可梦身上。并重洗牌库。"

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