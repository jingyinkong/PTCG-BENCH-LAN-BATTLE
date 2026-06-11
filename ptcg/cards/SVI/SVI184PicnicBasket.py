"""野餐篮 - SVI 184"""
from ptcg.core.action import UseItemAction
from ptcg.core.card import ItemCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.utils.utils import current_player, move_cards


class SVI184PicnicBasket(ItemCard):
    """野餐篮 - 道具卡。"""
    def __init__(self):
        super().__init__()
        self.set_name = "SVI"
        self.number = "184"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "野餐篮"
        self.cardType = CardType.NONE
        self.text = "将双方所有宝可梦的HP，各回复「30」。"

    def get_actions(self, state):
        actions = []
        player = current_player(state)
        actions.append(UseItemAction(player.id, self))
        return actions

    def reduce_action(self, action, state):
        if isinstance(action, UseItemAction):
            player = current_player(state)
            move_cards(self, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state)
            yield None