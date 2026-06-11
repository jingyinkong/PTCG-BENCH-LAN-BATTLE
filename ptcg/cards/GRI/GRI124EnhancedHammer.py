"""改造之锤 - GRI 124"""
from ptcg.core.action import UseItemAction
from ptcg.core.card import ItemCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.utils.utils import current_player, move_cards


class GRI124EnhancedHammer(ItemCard):
    """改造之锤 - 道具卡。"""
    def __init__(self):
        super().__init__()
        self.set_name = "GRI"
        self.number = "124"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "改造之锤"
        self.cardType = CardType.NONE
        self.text = "选择对手场上宝可梦身上附着的1个特殊能量，放于弃牌区。"

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