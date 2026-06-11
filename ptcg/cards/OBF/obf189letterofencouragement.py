"""鼓励信 - OBF 189"""
from ptcg.core.action import UseItemAction
from ptcg.core.card import ItemCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.utils.utils import current_player, move_cards


class OBF189LetterofEncouragement(ItemCard):
    """鼓励信 - 道具卡。"""
    def __init__(self):
        super().__init__()
        self.set_name = "OBF"
        self.number = "189"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "鼓励信"
        self.cardType = CardType.NONE
        self.text = "这张卡牌，只有在上一个对手的回合，自己的宝可梦【昏厥】时才可使用。  选择自己牌库中最多3张基本能量，在给对手看过之后，加入手牌。并重洗牌库。"

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