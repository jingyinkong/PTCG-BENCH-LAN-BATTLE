"""乌栗 - TWM 154"""
from ptcg.core.action import UseSupporterAction
from ptcg.core.card import SupporterCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.utils.utils import current_player, move_cards


class TWM154Kieran(SupporterCard):
    """乌栗 - 支援者卡。"""
    def __init__(self):
        super().__init__()
        self.set_name = "TWM"
        self.number = "154"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "乌栗"
        self.cardType = CardType.NONE
        self.text = "这张卡牌，从2个效果中选择1个使用。  ◆将自己的战斗宝可梦与备战宝可梦互换。  ◆在这个回合，自己宝可梦所使用的招式，给对手战斗场上的「宝可梦【ex】・V」造成的伤害「+30」。"

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