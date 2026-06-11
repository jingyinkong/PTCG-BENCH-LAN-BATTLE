"""空手道王的修炼 - PRE 096"""
from ptcg.core.action import UseSupporterAction
from ptcg.core.card import SupporterCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.utils.utils import current_player, move_cards


class PRE096BlackBeltsTraining(SupporterCard):
    """空手道王的修炼 - 支援者卡。"""
    def __init__(self):
        super().__init__()
        self.set_name = "PRE"
        self.number = "096"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "空手道王的修炼"
        self.cardType = CardType.NONE
        self.text = "在这个回合，自己宝可梦所使用的招式，给对手战斗场上的「宝可梦【ex】」造成的伤害「+40」。"

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