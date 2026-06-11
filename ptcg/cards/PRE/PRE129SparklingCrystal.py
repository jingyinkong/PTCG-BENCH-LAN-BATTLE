"""璀璨结晶 - PRE 129"""
from ptcg.core.action import UseItemAction
from ptcg.core.card import ToolCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.utils.utils import current_player, move_cards


class PRE129SparklingCrystal(ToolCard):
    """璀璨结晶 - 宝可梦道具卡。"""
    def __init__(self):
        super().__init__()
        self.set_name = "PRE"
        self.number = "129"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "璀璨结晶"
        self.cardType = CardType.NONE
        self.text = "身上放有这张卡牌的「太晶」宝可梦使用招式时，使用那个招式所需能量，减少1个。（减少的可以是任意属性的能量。）"

    def get_actions(self, state):
        actions = []
        player = current_player(state)
        actions.append(UseItemAction(player.id, self))
        return actions

    def reduce_action(self, action, state):
        if isinstance(action, UseItemAction):
            player = current_player(state)
            move_cards(self, (player.id, CardPosition.HAND), (player.id, CardPosition.DISCARD), state)
