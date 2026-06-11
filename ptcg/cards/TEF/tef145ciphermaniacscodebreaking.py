"""暗码迷的解读 - TEF 145"""
from ptcg.core.action import UseSupporterAction
from ptcg.core.card import SupporterCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.utils.utils import current_player, move_cards


class TEF145CiphermaniacsCodebreaking(SupporterCard):
    """暗码迷的解读 - 支援者卡。"""
    def __init__(self):
        super().__init__()
        self.set_name = "TEF"
        self.number = "145"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "暗码迷的解读"
        self.cardType = CardType.NONE
        self.text = "选择自己牌库中任意2张卡牌。将剩余的牌库重洗，将选择的卡牌以任意顺序重新排列，放回牌库上方。"

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