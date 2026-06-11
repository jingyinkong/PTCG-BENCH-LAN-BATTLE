"""厉害钓竿 - PAL 188"""
from ptcg.core.action import UseItemAction
from ptcg.core.card import ItemCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.utils.utils import current_player, move_cards


class PAL188SuperRod(ItemCard):
    """厉害钓竿 - 道具卡。"""
    def __init__(self):
        super().__init__()
        self.set_name = "PAL"
        self.number = "188"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "厉害钓竿"
        self.cardType = CardType.NONE
        self.text = "选择自己弃牌区中的宝可梦和基本能量合计最多3张，在给对手看过之后，放回牌库并重洗牌库。"

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