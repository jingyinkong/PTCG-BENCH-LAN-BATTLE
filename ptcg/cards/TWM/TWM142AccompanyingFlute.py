"""配乐之笛 - TWM 142"""
from ptcg.core.action import UseItemAction
from ptcg.core.card import ItemCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.utils.utils import current_player, move_cards


class TWM142AccompanyingFlute(ItemCard):
    """配乐之笛 - 道具卡。"""
    def __init__(self):
        super().__init__()
        self.set_name = "TWM"
        self.number = "142"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "配乐之笛"
        self.cardType = CardType.NONE
        self.text = "将对手牌库上方5张卡牌翻到正面，选择其中任意数量的【基础】宝可梦，放于对手的备战区。将剩余的卡牌放回牌库并重洗牌库。"

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