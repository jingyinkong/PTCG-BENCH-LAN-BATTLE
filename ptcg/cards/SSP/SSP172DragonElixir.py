"""龙之秘药 - SSP 172"""
from ptcg.core.action import UseItemAction
from ptcg.core.card import ItemCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.utils.utils import current_player, move_cards


class SSP172DragonElixir(ItemCard):
    """龙之秘药 - 道具卡。"""
    def __init__(self):
        super().__init__()
        self.set_name = "SSP"
        self.number = "172"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "龙之秘药"
        self.cardType = CardType.NONE
        self.text = "回复自己战斗场上【龙】宝可梦「60」HP。"

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