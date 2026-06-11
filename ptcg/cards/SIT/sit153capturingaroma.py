"""捕获香氛 - SIT 153"""
from ptcg.core.action import UseItemAction
from ptcg.core.card import ItemCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.utils.utils import current_player, move_cards


class SIT153CapturingAroma(ItemCard):
    """捕获香氛 - 道具卡。"""
    def __init__(self):
        super().__init__()
        self.set_name = "SIT"
        self.number = "153"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "捕获香氛"
        self.cardType = CardType.NONE
        self.text = "抛掷1次硬币。如果为正面则从自己牌库中选择1张进化宝可梦，如果为反面则从自己牌库中选择1张【基础】宝可梦，在给对手看过之后，加入手牌。并重洗牌库。"

    def get_actions(self, state):
        actions = []
        player = current_player(state)
        if self in player.hand:
            actions.append(UseItemAction(player.id, self))
        return actions

    def reduce_action(self, action, state):
        if isinstance(action, UseItemAction):
            player = current_player(state)
            move_cards(self, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state)
            yield None