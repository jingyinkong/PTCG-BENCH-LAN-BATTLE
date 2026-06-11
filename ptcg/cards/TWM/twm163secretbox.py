"""秘密箱 - TWM 163"""
from ptcg.core.action import UseItemAction
from ptcg.core.card import ItemCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.utils.utils import current_player, move_cards


class TWM163SecretBox(ItemCard):
    """秘密箱 - 道具卡。"""
    def __init__(self):
        super().__init__()
        self.set_name = "TWM"
        self.number = "163"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "秘密箱"
        self.cardType = CardType.NONE
        self.cardPosition = CardPosition.DECK
        self.text = "这张卡牌，只有将自己的3张手牌放于弃牌区后才可使用。   选择自己牌库中「物品」「宝可梦道具」「支援者」「竞技场」各1张，在给对手看过之后，加入手牌。并重洗牌库。"

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