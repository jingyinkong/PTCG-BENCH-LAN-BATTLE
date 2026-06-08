"""Trekking Shoes - ASR 156"""
from ptcg.core.action import UseItemAction
from ptcg.core.card import ItemCard
from ptcg.core.enums import CardPosition, CardType
from ptcg.utils.utils import current_player, move_cards


class ASR156TrekkingShoes(ItemCard):
    """Trekking Shoes - Item. Look at top card of deck, may discard it, then draw 1."""
    def __init__(self):
        super().__init__()
        self.set_name = "ASR"
        self.number = "156"
        self.id = f"{self.set_name}-{self.number}"
        self.name = "离洞绳"
        self.cardType = CardType.NONE
        self.text = "查看自己牌库上方的1张卡牌。可选择将其丢于弃牌区。然后，从自己的牌库上方抽取1张卡牌。"

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
            # 查看牌库顶并可选弃掉
            if player.left:
                top = player.left[0]
                move_cards(top, (player.id, CardPosition.LEFT), (player.id, CardPosition.DISCARD), state)
            # 抽1张
            if player.left:
                move_cards(player.left[0], (player.id, CardPosition.LEFT), (player.id, CardPosition.HAND), state)
