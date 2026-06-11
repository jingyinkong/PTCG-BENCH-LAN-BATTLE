"""交替推车 - ASR 154"""
from ptcg.core.action import UseItemAction
from ptcg.core.card import ItemCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.utils.utils import current_player, move_cards


class ASR154SwitchCart(ItemCard):
    """交替推车 - 道具卡。"""
    def __init__(self):
        super().__init__()
        self.set_name = "ASR"
        self.number = "154"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "交替推车"
        self.cardType = CardType.NONE
        self.text = "将自己战斗场上的【基础】宝可梦与备战宝可梦互换。然后，回复被换入备战区的宝可梦「30」点HP。"

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